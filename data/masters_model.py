#!/usr/bin/env python3
"""
Masters 2026 Prediction Model
Trains XGBoost models on player features + historical Masters results
to predict win %, top-5, top-10, top-20, and make-cut probabilities.

Run: python3 data/masters_model.py
"""

import json
import urllib.request
import urllib.parse
import ssl
import numpy as np
import pandas as pd
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
import warnings
warnings.filterwarnings('ignore')

SUPABASE_URL = "https://kakjbyoxqjvwnsdbqcnb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtha2pieW94cWp2d25zZGJxY25iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk0NzQxMjgsImV4cCI6MjA4NTA1MDEyOH0.6kkaabg_8D2qKcIsuEUVuZWja3LIdx8-a2wwoTmu30k"
ctx = ssl.create_default_context()

def sb_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())

def sb_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json", "Prefer": "return=minimal"
    }
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            return True
    except urllib.error.HTTPError as e:
        print(f"  POST error: {e.read().decode()[:200]}")
        return False

def sb_delete(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            return True
    except:
        return False

# =========================================================================
# FEATURE ENGINEERING
# =========================================================================

FEATURES = [
    'sg_approach', 'sg_off_tee', 'sg_around_green', 'sg_putting',
    'spike_approach_events', 'masters_appearances', 'masters_cuts_made',
    'best_masters_finish', 'betting_odds', 'recent_form_avg_finish',
    'par5_scoring_avg', 'scrambling_pct', 'days_since_last_event'
]

def build_training_data(field_df, results_df):
    """
    Build training dataset by joining historical results with player features.
    Uses current features as proxy for general player skill level.
    """
    # For each historical result, look up player's current features
    training_rows = []

    for _, result in results_df.iterrows():
        player = field_df[field_df['player_name'] == result['player_name']]
        if player.empty:
            continue
        player = player.iloc[0]

        # Skip if missing key features
        if pd.isna(player.get('sg_approach')):
            continue

        row = {}
        for f in FEATURES:
            row[f] = float(player[f]) if pd.notna(player.get(f)) else None

        # Target variables
        if result['made_cut']:
            finish = int(result['finish_position']) if pd.notna(result['finish_position']) else 50
            row['finish_position'] = finish
            row['is_winner'] = 1 if finish == 1 else 0
            row['is_top5'] = 1 if finish <= 5 else 0
            row['is_top10'] = 1 if finish <= 10 else 0
            row['is_top20'] = 1 if finish <= 20 else 0
            row['made_cut'] = 1
        else:
            row['finish_position'] = 60  # placeholder for missed cut
            row['is_winner'] = 0
            row['is_top5'] = 0
            row['is_top10'] = 0
            row['is_top20'] = 0
            row['made_cut'] = 0

        row['player_name'] = result['player_name']
        row['year'] = result['year']
        training_rows.append(row)

    return pd.DataFrame(training_rows)


def train_models(train_df):
    """Train XGBoost models for each target variable."""

    # Drop rows with any missing features
    feature_cols = [f for f in FEATURES if f in train_df.columns]
    clean = train_df.dropna(subset=feature_cols)
    X = clean[feature_cols].astype(float)

    print(f"\n  Training data: {len(clean)} rows, {len(feature_cols)} features")
    print(f"  Positive rates: win={clean['is_winner'].mean():.3f}, top5={clean['is_top5'].mean():.3f}, "
          f"top10={clean['is_top10'].mean():.3f}, top20={clean['is_top20'].mean():.3f}, cut={clean['made_cut'].mean():.3f}")

    models = {}
    targets = {
        'win': 'is_winner',
        'top5': 'is_top5',
        'top10': 'is_top10',
        'top20': 'is_top20',
        'make_cut': 'made_cut'
    }

    for name, col in targets.items():
        y = clean[col].astype(int)

        # Handle class imbalance with scale_pos_weight
        n_neg = (y == 0).sum()
        n_pos = max((y == 1).sum(), 1)
        spw = n_neg / n_pos

        model = XGBClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            scale_pos_weight=spw,
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42,
            min_child_weight=2,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.5,
            reg_lambda=1.0
        )

        # Cross-validate
        scores = cross_val_score(model, X, y, cv=min(5, len(clean) // 5), scoring='roc_auc')
        print(f"  {name}: CV AUC = {scores.mean():.3f} (+/- {scores.std():.3f})")

        # Fit on full data
        model.fit(X, y)
        models[name] = model

    # Also train a regressor for predicted finish position
    y_finish = clean['finish_position'].astype(float)
    reg = XGBRegressor(
        n_estimators=100, max_depth=3, learning_rate=0.1,
        random_state=42, min_child_weight=2, subsample=0.8,
        colsample_bytree=0.8, reg_alpha=0.5, reg_lambda=1.0
    )
    scores = cross_val_score(reg, X, y_finish, cv=min(5, len(clean) // 5), scoring='neg_mean_absolute_error')
    print(f"  finish_pos: CV MAE = {-scores.mean():.1f} (+/- {scores.std():.1f})")
    reg.fit(X, y_finish)
    models['finish'] = reg

    # Feature importance
    print("\n  Feature Importance (win model):")
    importances = models['win'].feature_importances_
    fi = sorted(zip(feature_cols, importances), key=lambda x: -x[1])
    for feat, imp in fi:
        bar = '█' * int(imp * 50)
        print(f"    {feat:30s} {imp:.3f} {bar}")

    return models, feature_cols


def predict_field(models, field_df, feature_cols):
    """Generate predictions for the entire 2026 field."""
    predictions = []

    for _, player in field_df.iterrows():
        name = player['player_name']

        # Check if we have enough features
        feature_vals = []
        has_data = True
        for f in feature_cols:
            val = player.get(f)
            if pd.isna(val) or val is None:
                has_data = False
                break
            feature_vals.append(float(val))

        if not has_data:
            # Use market odds as a fallback for players without full features
            odds = float(player.get('betting_odds', 50000))
            implied = 100 / (odds + 100) if odds > 0 else 0.01
            predictions.append({
                'player_name': name,
                'predicted_finish': 50.0,
                'win_probability': round(implied * 0.8, 4),  # Discount market odds slightly
                'top5_probability': round(min(implied * 4, 0.5), 4),
                'top10_probability': round(min(implied * 7, 0.7), 4),
                'top20_probability': round(min(implied * 12, 0.85), 4),
                'make_cut_probability': round(min(implied * 20, 0.95), 4),
                'confidence_score': 0.3,  # Low confidence — market-only estimate
                'model_name': 'xgb_masters_v1',
                'model_version': '1.0-market-fallback'
            })
            continue

        X = np.array([feature_vals])

        # Get probabilities
        win_prob = float(models['win'].predict_proba(X)[0][1])
        top5_prob = float(models['top5'].predict_proba(X)[0][1])
        top10_prob = float(models['top10'].predict_proba(X)[0][1])
        top20_prob = float(models['top20'].predict_proba(X)[0][1])
        cut_prob = float(models['make_cut'].predict_proba(X)[0][1])
        pred_finish = float(models['finish'].predict(X)[0])

        # Ensure monotonicity: win < top5 < top10 < top20 < cut
        top5_prob = max(top5_prob, win_prob)
        top10_prob = max(top10_prob, top5_prob)
        top20_prob = max(top20_prob, top10_prob)
        cut_prob = max(cut_prob, top20_prob)

        predictions.append({
            'player_name': name,
            'predicted_finish': round(max(1, min(pred_finish, 60)), 1),
            'win_probability': round(win_prob, 4),
            'top5_probability': round(top5_prob, 4),
            'top10_probability': round(top10_prob, 4),
            'top20_probability': round(top20_prob, 4),
            'make_cut_probability': round(cut_prob, 4),
            'confidence_score': 0.75,
            'model_name': 'xgb_masters_v1',
            'model_version': '1.0'
        })

    return pd.DataFrame(predictions)


def normalize_probabilities(preds_df):
    """Normalize win probabilities to sum to ~100% (like a real probability distribution)."""
    total_win = preds_df['win_probability'].sum()
    if total_win > 0:
        scale = 1.0 / total_win
        preds_df['win_probability'] = (preds_df['win_probability'] * scale).round(4)
    return preds_df


def main():
    print("=" * 60)
    print("  MASTERS 2026 PREDICTION MODEL")
    print("=" * 60)

    # Load data
    print("\n[1/5] Loading data from Supabase...")
    field_raw = sb_get('masters_field_2026', 'select=*')
    results_raw = sb_get('masters_player_results', 'select=*')

    field_df = pd.DataFrame(field_raw)
    results_df = pd.DataFrame(results_raw)
    print(f"  Field: {len(field_df)} players")
    print(f"  Historical results: {len(results_df)} rows")

    # Build training data
    print("\n[2/5] Building training dataset...")
    train_df = build_training_data(field_df, results_df)
    print(f"  Training rows (with features): {len(train_df)}")

    # Train models
    print("\n[3/5] Training XGBoost models...")
    models, feature_cols = train_models(train_df)

    # Generate predictions
    print("\n[4/5] Generating predictions for 2026 field...")
    preds_df = predict_field(models, field_df, feature_cols)
    preds_df = normalize_probabilities(preds_df)

    # Sort by win probability
    preds_df = preds_df.sort_values('win_probability', ascending=False).reset_index(drop=True)

    # Display top 20
    print("\n" + "=" * 60)
    print("  TOP 20 PREDICTIONS")
    print("=" * 60)
    print(f"\n  {'#':>3}  {'Player':<25} {'Win%':>6} {'Top5':>6} {'Top10':>6} {'Top20':>6} {'Cut':>6} {'Finish':>6}")
    print("  " + "-" * 85)

    for i, row in preds_df.head(20).iterrows():
        idx = preds_df.index.get_loc(i) + 1
        print(f"  {idx:>3}  {row['player_name']:<25} {row['win_probability']*100:>5.1f}% {row['top5_probability']*100:>5.1f}% "
              f"{row['top10_probability']*100:>5.1f}% {row['top20_probability']*100:>5.1f}% "
              f"{row['make_cut_probability']*100:>5.1f}% {row['predicted_finish']:>5.1f}")

    # Value picks (model win% significantly higher than implied odds)
    print("\n" + "=" * 60)
    print("  VALUE PICKS (Model vs Market)")
    print("=" * 60)

    for _, row in preds_df.iterrows():
        player = field_df[field_df['player_name'] == row['player_name']].iloc[0]
        market_implied = float(player['implied_probability']) / 100
        model_win = row['win_probability']
        edge = model_win - market_implied

        if edge > 0.005 and row['confidence_score'] >= 0.7:
            odds = int(player['betting_odds'])
            print(f"  {row['player_name']:<25} Model: {model_win*100:>5.1f}%  Market: {market_implied*100:>5.1f}%  "
                  f"Edge: +{edge*100:.1f}%  Odds: +{odds}")

    # Store predictions in Supabase
    print(f"\n[5/5] Storing predictions in Supabase...")

    # Clear old predictions
    sb_delete('masters_predictions', 'model_name=eq.xgb_masters_v1')

    stored = 0
    for _, row in preds_df.iterrows():
        record = {
            'model_name': row['model_name'],
            'model_version': row['model_version'],
            'player_name': row['player_name'],
            'predicted_finish': float(row['predicted_finish']),
            'win_probability': float(row['win_probability']),
            'top5_probability': float(row['top5_probability']),
            'top10_probability': float(row['top10_probability']),
            'top20_probability': float(row['top20_probability']),
            'make_cut_probability': float(row['make_cut_probability']),
            'confidence_score': float(row['confidence_score'])
        }
        if sb_post('masters_predictions', record):
            stored += 1

    print(f"  Stored {stored}/{len(preds_df)} predictions")
    print("\n✓ Model training complete. Predictions live in Supabase.")


if __name__ == '__main__':
    main()
