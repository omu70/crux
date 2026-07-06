"""Predictive models: CTR, CVR, CPA, ROAS, creative quality, win probability,
audience match.

Two tiers:
  1. Heuristic cold-start (always available, model_version "heuristic-v1") —
     calibrated scoring functions over extracted features.
  2. Learned tier — when a client accumulates enough labelled history
     (campaign rows with spend + outcomes), gradient-boosted models are
     trained per-account via scikit-learn IF installed, persisted to
     backend/uploads/models/, and take over (model_version "gbm-v1").

The learned tier is optional by design: sklearn is a heavy dependency, so the
platform degrades gracefully to heuristics without it.
"""
from __future__ import annotations

import logging
import math
import os
import pickle
from typing import Any

from app.ml.features import campaign_features, creative_text_features

log = logging.getLogger("aether.ml")

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "models")
MIN_TRAINING_ROWS = 25


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


# ── Tier 1: heuristic creative-quality / CTR predictor ───────────────────────
def predict_creative(text: str, kind: str, framework: str) -> dict[str, float]:
    """Score a creative asset 0-100 + predicted CTR%. Deterministic heuristic
    tuned to reward direct-response fundamentals."""
    f = creative_text_features(text, kind, framework)

    score = 50.0
    # hook strength: short punchy first line, second person, curiosity
    score += min(10, f["second_person"] * 120)
    score += 6 if 4 <= f["first_line_len"] <= 12 else -4
    score += min(8, f["power_word_ratio"] * 80)
    score += min(8, f["emotion_word_ratio"] * 90)
    score += 4 if f["has_cta_verb"] else -3
    score += 3 if f["question_marks"] >= 1 else 0
    score += 3 if f["digits"] >= 1 else 0
    # readability
    score += 4 if f["words_per_sentence"] <= 16 else -5
    score += 3 if f["line_breaks"] >= 2 and f["word_count"] > 40 else 0
    # penalties
    score -= 6 if f["caps_ratio"] > 0.3 else 0
    score -= 4 if f["exclamations"] > 3 else 0
    score -= 5 if f["word_count"] > 220 else 0
    score = max(5.0, min(98.0, score))

    ctr = round(0.4 + (score / 100) * 2.4, 2)  # 0.4–2.8% typical feed range
    return {"creative_quality": round(score, 1), "ctr": ctr,
            "win_probability": round(_sigmoid((score - 62) / 10), 3)}


# ── Tier 1: heuristic campaign outcome predictor ─────────────────────────────
def predict_campaign(campaign: Any, target_cpa: float | None = None) -> dict[str, float]:
    f = campaign_features(campaign)
    ctr = f["ctr"]
    roas = f["roas"]
    freq = f["frequency"]

    # win probability blends efficiency vs benchmarks and fatigue headroom
    z = 0.0
    z += (ctr - 1.2) * 0.9            # CTR vs feed benchmark
    z += (roas - 2.0) * 0.55          # ROAS vs breakeven-ish benchmark
    z -= max(0.0, freq - 2.5) * 0.5   # fatigue drag
    z += 0.3 if f["conversions"] >= 20 else -0.2  # signal volume
    win = _sigmoid(z)

    cvr = min(12.0, max(0.2, (f["conversions"] / max(1.0, f["ctr"] * f["impressions"] / 100)) * 100)) \
        if f["impressions"] > 100 else 1.8
    cpa_pred = f["cpa"] if f["cpa"] > 0 else (f["spend"] / max(1, f["conversions"]) if f["conversions"] else 0.0)

    return {
        "ctr": round(ctr, 2), "cvr": round(cvr, 2),
        "cpa": round(cpa_pred, 2), "roas": round(max(0.0, roas), 2),
        "win_probability": round(win, 3),
        "audience_match": round(_sigmoid((ctr - 1.0) * 1.2 - max(0, freq - 3) * 0.4), 3),
        "creative_quality": round(min(98, 40 + ctr * 20), 1),
    }


# ── Tier 2: learned models (optional sklearn) ────────────────────────────────
def _sklearn_available() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False


def _model_path(client_id: str, target: str) -> str:
    os.makedirs(MODELS_DIR, exist_ok=True)
    return os.path.join(MODELS_DIR, f"{client_id}_{target}.pkl")


def train_account_models(db, client_id: str) -> dict[str, Any]:
    """Train per-account GBMs on historical campaigns. Returns training report."""
    if not _sklearn_available():
        return {"trained": False, "reason": "scikit-learn not installed; heuristic tier active"}

    from app.models.models import Campaign
    rows = (db.query(Campaign).filter(Campaign.client_id == client_id,
                                      Campaign.spend > 0).all())
    if len(rows) < MIN_TRAINING_ROWS:
        return {"trained": False,
                "reason": f"need >= {MIN_TRAINING_ROWS} spent campaigns, have {len(rows)}"}

    from sklearn.ensemble import GradientBoostingRegressor
    feature_names = ["spend", "impressions", "cpm", "frequency", "reach_ratio"]
    X = [[campaign_features(c)[k] for k in feature_names] for c in rows]
    report: dict[str, Any] = {"trained": True, "rows": len(rows), "targets": {}}
    for target, getter in (("ctr", lambda c: c.ctr or 0),
                           ("roas", lambda c: c.purchase_roas or 0),
                           ("cpa", lambda c: c.cpa or 0)):
        y = [getter(c) for c in rows]
        model = GradientBoostingRegressor(n_estimators=120, max_depth=3, learning_rate=0.08)
        model.fit(X, y)
        with open(_model_path(client_id, target), "wb") as fh:
            pickle.dump({"model": model, "features": feature_names, "version": "gbm-v1"}, fh)
        report["targets"][target] = {"r2_in_sample": round(float(model.score(X, y)), 3)}
    return report


def predict_with_learned(client_id: str, campaign: Any) -> dict[str, float] | None:
    """Use trained account models when present; None → caller falls back."""
    if not _sklearn_available():
        return None
    out: dict[str, float] = {}
    f = campaign_features(campaign)
    for target in ("ctr", "roas", "cpa"):
        path = _model_path(client_id, target)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as fh:
                bundle = pickle.load(fh)
            x = [[f[k] for k in bundle["features"]]]
            out[target] = round(float(bundle["model"].predict(x)[0]), 3)
        except Exception as exc:
            log.warning("learned prediction failed (%s): %s", target, exc)
            return None
    heur = predict_campaign(campaign)
    return {**heur, **out, "model_version": "gbm-v1"}
