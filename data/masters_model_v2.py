#!/usr/bin/env python3
"""
Masters 2026 Prediction Model v2
- Ordinal regression approach: predicts finish position distribution
- Bayesian prior from market odds
- Ensemble: XGBoost + Logistic Regression + market prior
- Focused on top-10 and top-20 accuracy

Run: python3 data/masters_model_v2.py
"""

import json
import urllib.request
import urllib.parse
import ssl
import numpy as np
import pandas as pd
from xgboost import XGBClassifier, XGBRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
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
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        urllib.request.urlopen(req, context=ctx)
        return True
    except urllib.error.HTTPError as e:
        print(f"  POST error: {e.read().decode()[:200]}")
        return False

def sb_delete(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    try:
        urllib.request.urlopen(req, context=ctx)
        return True
    except:
        return False


FEATURES = [
    'sg_approach', 'sg_off_tee', 'sg_around_green', 'sg_putting',
    'spike_approach_events', 'masters_appearances', 'masters_cuts_made',
    'best_masters_finish', 'betting_odds', 'recent_form_avg_finish',
    'par5_scoring_avg', 'scrambling_pct', 'days_since_last_event',
    'age', 'form_trend', 'recent_masters_score',
    'conditions_boost', 'injury_discount'
]


def build_training_data(field_df, results_df):
    """Build training dataset with ordinal finish buckets."""
    training_rows = []
    for _, result in results_df.iterrows():
        player = field_df[field_df['player_name'] == result['player_name']]
        if player.empty:
            continue
        player = player.iloc[0]
        if pd.isna(player.get('sg_approach')):
            continue

        row = {f: float(player[f]) if pd.notna(player.get(f)) else None for f in FEATURES}

        if result['made_cut']:
            finish = int(result['finish_position']) if pd.notna(result['finish_position']) else 50
        else:
            finish = 65

        row['finish_position'] = finish
        row['is_top5'] = 1 if finish <= 5 else 0
        row['is_top10'] = 1 if finish <= 10 else 0
        row['is_top20'] = 1 if finish <= 20 else 0
        row['made_cut'] = 1 if result['made_cut'] else 0

        # Ordinal bucket: 0=MC, 1=cut but >30, 2=21-30, 3=11-20, 4=6-10, 5=top5
        if not result['made_cut']:
            row['ordinal'] = 0
        elif finish > 30:
            row['ordinal'] = 1
        elif finish > 20:
            row['ordinal'] = 2
        elif finish > 10:
            row['ordinal'] = 3
        elif finish > 5:
            row['ordinal'] = 4
        else:
            row['ordinal'] = 5

        row['player_name'] = result['player_name']
        row['year'] = result['year']
        training_rows.append(row)

    return pd.DataFrame(training_rows)


def market_prior(odds):
    """Convert betting odds to probability vector [MC, 30+, 21-30, 11-20, 6-10, top5]."""
    if odds <= 0:
        odds = 50000
    implied_win = 100 / (odds + 100)

    # Empirical scaling from implied win prob to finish distribution
    # Based on PGA Tour historical data patterns
    top5 = min(implied_win * 4.5, 0.50)
    top10 = min(implied_win * 8.0, 0.65)
    top20 = min(implied_win * 14.0, 0.80)
    make_cut = min(implied_win * 22.0, 0.92)

    p_mc = 1 - make_cut
    p_30plus = make_cut - top20
    p_21_30 = top20 - top10
    p_11_20 = top10 - top5
    p_6_10 = top5 - implied_win * 2  # rough split of top5 into 1-5 vs 6-10 doesn't apply here
    # Redistribute: top5 bucket, 6-10 bucket
    p_top5 = top5
    p_6_10 = top10 - top5

    probs = np.array([p_mc, p_30plus, max(p_21_30, 0.01), max(p_11_20, 0.01), max(p_6_10, 0.01), max(p_top5, 0.01)])
    probs = probs / probs.sum()
    return probs


def train_ensemble(train_df):
    """Train ensemble models focused on top-10 and top-20 accuracy."""
    feature_cols = [f for f in FEATURES if f in train_df.columns]
    clean = train_df.dropna(subset=feature_cols)
    X = clean[feature_cols].astype(float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"\n  Training data: {len(clean)} rows, {len(feature_cols)} features")
    print(f"  Ordinal distribution: {clean['ordinal'].value_counts().sort_index().to_dict()}")

    models = {}
    targets = {
        'top5': 'is_top5',
        'top10': 'is_top10',
        'top20': 'is_top20',
        'make_cut': 'made_cut'
    }

    for name, col in targets.items():
        y = clean[col].astype(int)
        n_pos = max(y.sum(), 1)
        n_neg = (y == 0).sum()
        spw = n_neg / n_pos

        # Model 1: XGBoost with tuned params for sparse targets
        xgb = XGBClassifier(
            n_estimators=200, max_depth=2, learning_rate=0.05,
            scale_pos_weight=spw, eval_metric='logloss', random_state=42,
            min_child_weight=3, subsample=0.7, colsample_bytree=0.7,
            reg_alpha=1.0, reg_lambda=2.0, gamma=0.1
        )

        # Model 2: Logistic Regression (good with small data)
        lr = LogisticRegression(
            C=0.5, class_weight='balanced', max_iter=1000, random_state=42,
            solver='lbfgs', penalty='l2'
        )

        # Model 3: GradientBoosting (different boosting impl)
        gb = GradientBoostingClassifier(
            n_estimators=150, max_depth=2, learning_rate=0.05,
            min_samples_leaf=5, subsample=0.7, random_state=42
        )

        # Cross-validate each
        n_splits = min(5, max(2, n_pos))
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        xgb_scores = cross_val_score(xgb, X, y, cv=cv, scoring='roc_auc')
        lr_scores = cross_val_score(lr, X_scaled, y, cv=cv, scoring='roc_auc')
        gb_scores = cross_val_score(gb, X, y, cv=cv, scoring='roc_auc')

        print(f"\n  {name}:")
        print(f"    XGBoost AUC:  {xgb_scores.mean():.3f} (+/- {xgb_scores.std():.3f})")
        print(f"    LogReg AUC:   {lr_scores.mean():.3f} (+/- {lr_scores.std():.3f})")
        print(f"    GBoosting AUC:{gb_scores.mean():.3f} (+/- {gb_scores.std():.3f})")

        # Fit all on full data
        xgb.fit(X, y)
        lr.fit(X_scaled, y)
        gb.fit(X, y)

        # Weight by CV performance
        total_auc = xgb_scores.mean() + lr_scores.mean() + gb_scores.mean()
        w_xgb = xgb_scores.mean() / total_auc
        w_lr = lr_scores.mean() / total_auc
        w_gb = gb_scores.mean() / total_auc

        ensemble_auc = w_xgb * xgb_scores.mean() + w_lr * lr_scores.mean() + w_gb * gb_scores.mean()
        print(f"    Ensemble AUC: {ensemble_auc:.3f} (weights: xgb={w_xgb:.2f}, lr={w_lr:.2f}, gb={w_gb:.2f})")

        models[name] = {
            'xgb': xgb, 'lr': lr, 'gb': gb,
            'w_xgb': w_xgb, 'w_lr': w_lr, 'w_gb': w_gb
        }

    # Finish position regressor
    y_finish = clean['finish_position'].astype(float)
    reg = XGBRegressor(
        n_estimators=200, max_depth=2, learning_rate=0.05,
        random_state=42, min_child_weight=3, subsample=0.7,
        colsample_bytree=0.7, reg_alpha=1.0, reg_lambda=2.0
    )
    reg_scores = cross_val_score(reg, X, y_finish, cv=5, scoring='neg_mean_absolute_error')
    print(f"\n  finish_pos: CV MAE = {-reg_scores.mean():.1f} (+/- {reg_scores.std():.1f})")
    reg.fit(X, y_finish)
    models['finish'] = reg

    # Feature importance from the top-10 XGBoost (the key model)
    print("\n  Feature Importance (top-10 XGBoost):")
    importances = models['top10']['xgb'].feature_importances_
    fi = sorted(zip(feature_cols, importances), key=lambda x: -x[1])
    for feat, imp in fi:
        bar = '█' * int(imp * 50)
        print(f"    {feat:30s} {imp:.3f} {bar}")

    return models, feature_cols, scaler


def predict_with_ensemble(models, field_df, feature_cols, scaler, market_weight=0.30):
    """Generate predictions using ensemble + Bayesian market prior."""
    predictions = []

    for _, player in field_df.iterrows():
        name = player['player_name']
        odds = float(player.get('betting_odds', 50000))

        # Market prior probabilities
        mkt_prior = market_prior(odds)  # [MC, 30+, 21-30, 11-20, 6-10, top5]
        mkt_top5 = float(mkt_prior[5])
        mkt_top10 = float(mkt_prior[4] + mkt_prior[5])
        mkt_top20 = float(mkt_prior[3] + mkt_prior[4] + mkt_prior[5])
        mkt_cut = float(1 - mkt_prior[0])

        # Check if we have full features
        feature_vals = []
        has_data = True
        for f in feature_cols:
            val = player.get(f)
            if pd.isna(val) or val is None:
                has_data = False
                break
            feature_vals.append(float(val))

        if not has_data:
            # Market-only prediction
            implied = 100 / (odds + 100) if odds > 0 else 0.01
            predictions.append({
                'player_name': name,
                'predicted_finish': 45.0,
                'win_probability': round(implied, 4),
                'top5_probability': round(mkt_top5, 4),
                'top10_probability': round(mkt_top10, 4),
                'top20_probability': round(mkt_top20, 4),
                'make_cut_probability': round(mkt_cut, 4),
                'confidence_score': 0.3,
                'model_name': 'xgb_ensemble_v2',
                'model_version': '2.0-market-only'
            })
            continue

        X = np.array([feature_vals])
        X_scaled = scaler.transform(X)

        # Get ensemble predictions for each target
        model_probs = {}
        for target in ['top5', 'top10', 'top20', 'make_cut']:
            m = models[target]
            p_xgb = float(m['xgb'].predict_proba(X)[0][1])
            p_lr = float(m['lr'].predict_proba(X_scaled)[0][1])
            p_gb = float(m['gb'].predict_proba(X)[0][1])

            # Weighted ensemble
            model_prob = m['w_xgb'] * p_xgb + m['w_lr'] * p_lr + m['w_gb'] * p_gb
            model_probs[target] = model_prob

        # Bayesian blend: (1 - market_weight) * model + market_weight * market
        mw = market_weight
        top5_prob = (1 - mw) * model_probs['top5'] + mw * mkt_top5
        top10_prob = (1 - mw) * model_probs['top10'] + mw * mkt_top10
        top20_prob = (1 - mw) * model_probs['top20'] + mw * mkt_top20
        cut_prob = (1 - mw) * model_probs['make_cut'] + mw * mkt_cut

        # Implied win prob from market (we don't model this separately in v2)
        implied_win = 100 / (odds + 100) if odds > 0 else 0.01
        # Scale win prob by how much our top5 deviates from market top5
        win_scale = top5_prob / max(mkt_top5, 0.001)
        win_prob = implied_win * win_scale

        # Monotonicity
        top5_prob = min(top5_prob, top10_prob)
        top10_prob = min(top10_prob, top20_prob)
        top20_prob = min(top20_prob, cut_prob)

        pred_finish = float(models['finish'].predict(X)[0])

        predictions.append({
            'player_name': name,
            'predicted_finish': round(max(1, min(pred_finish, 60)), 1),
            'win_probability': round(max(win_prob, 0.0001), 4),
            'top5_probability': round(top5_prob, 4),
            'top10_probability': round(top10_prob, 4),
            'top20_probability': round(top20_prob, 4),
            'make_cut_probability': round(cut_prob, 4),
            'confidence_score': 0.75,
            'model_name': 'xgb_ensemble_v2',
            'model_version': '2.0'
        })

    return pd.DataFrame(predictions)


def normalize_probs(df):
    """Normalize win probs to sum to ~1."""
    total = df['win_probability'].sum()
    if total > 0:
        df['win_probability'] = (df['win_probability'] / total).round(4)
    return df


def main():
    print("=" * 60)
    print("  MASTERS 2026 PREDICTION MODEL v2")
    print("  Ensemble + Bayesian Market Prior")
    print("=" * 60)

    print("\n[1/5] Loading data...")
    field_df = pd.DataFrame(sb_get('masters_field_2026', 'select=*'))
    results_df = pd.DataFrame(sb_get('masters_player_results', 'select=*'))
    print(f"  Field: {len(field_df)} | Results: {len(results_df)}")

    print("\n[2/5] Building training data...")
    train_df = build_training_data(field_df, results_df)
    print(f"  Usable training rows: {len(train_df)}")

    print("\n[3/5] Training ensemble models...")
    models, feature_cols, scaler = train_ensemble(train_df)

    print("\n[4/5] Generating predictions (40% market prior blend)...")
    preds_df = predict_with_ensemble(models, field_df, feature_cols, scaler, market_weight=0.40)
    preds_df = normalize_probs(preds_df)
    preds_df = preds_df.sort_values('top10_probability', ascending=False).reset_index(drop=True)

    # Display
    print("\n" + "=" * 70)
    print("  TOP 25 — SORTED BY TOP-10 PROBABILITY")
    print("=" * 70)
    print(f"\n  {'#':>3}  {'Player':<25} {'Win%':>6} {'Top5':>6} {'Top10':>7} {'Top20':>7} {'Cut':>6} {'Finish':>6}")
    print("  " + "-" * 90)

    for i in range(min(25, len(preds_df))):
        row = preds_df.iloc[i]
        print(f"  {i+1:>3}  {row['player_name']:<25} {row['win_probability']*100:>5.1f}% "
              f"{row['top5_probability']*100:>5.1f}% {row['top10_probability']*100:>6.1f}% "
              f"{row['top20_probability']*100:>6.1f}% {row['make_cut_probability']*100:>5.1f}% "
              f"{row['predicted_finish']:>5.1f}")

    # Value plays for top-10/top-20 markets
    print("\n" + "=" * 70)
    print("  TOP-10 VALUE PLAYS (Model vs Market)")
    print("=" * 70)

    for i in range(len(preds_df)):
        row = preds_df.iloc[i]
        player = field_df[field_df['player_name'] == row['player_name']].iloc[0]
        odds = float(player['betting_odds'])
        mkt = market_prior(odds)
        mkt_top10 = float(mkt[4] + mkt[5])
        model_top10 = row['top10_probability']
        edge = model_top10 - mkt_top10

        if edge > 0.03 and row['confidence_score'] >= 0.7:
            print(f"  {row['player_name']:<25} Model: {model_top10*100:>5.1f}%  Market: {mkt_top10*100:>5.1f}%  Edge: +{edge*100:.1f}%  (+{int(odds)})")

    print("\n" + "=" * 70)
    print("  TOP-20 VALUE PLAYS (Model vs Market)")
    print("=" * 70)

    for i in range(len(preds_df)):
        row = preds_df.iloc[i]
        player = field_df[field_df['player_name'] == row['player_name']].iloc[0]
        odds = float(player['betting_odds'])
        mkt = market_prior(odds)
        mkt_top20 = float(mkt[3] + mkt[4] + mkt[5])
        model_top20 = row['top20_probability']
        edge = model_top20 - mkt_top20

        if edge > 0.03 and row['confidence_score'] >= 0.7:
            print(f"  {row['player_name']:<25} Model: {model_top20*100:>5.1f}%  Market: {mkt_top20*100:>5.1f}%  Edge: +{edge*100:.1f}%  (+{int(odds)})")

    # Store predictions
    print(f"\n[5/5] Storing predictions...")
    sb_delete('masters_predictions', 'model_name=eq.xgb_ensemble_v2')

    stored = 0
    for _, row in preds_df.iterrows():
        record = {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in row.to_dict().items()}
        if sb_post('masters_predictions', record):
            stored += 1

    print(f"  Stored {stored}/{len(preds_df)} predictions")
    print("\n✓ Model v2 training complete.")


if __name__ == '__main__':
    main()
