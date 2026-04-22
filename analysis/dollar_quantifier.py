"""
analysis/dollar_quantifier.py — Converts LeakageFlags to dollar estimates.

Deduplication: a deal flagged by multiple scorers uses the HIGHEST
estimated loss — not additive — to avoid double-counting.
"""
from dataclasses import dataclass, field
from typing import Optional
from config import AVG_DEAL_VALUE


@dataclass
class LeakageSummary:
    total_pipeline_value: float
    total_estimated_leakage: float
    leakage_pct: float
    deals_flagged: int
    total_deals: int
    critical_count: int
    high_count: int
    medium_count: int
    by_scorer: dict = field(default_factory=dict)
    by_stage: dict = field(default_factory=dict)
    top_flags: list = field(default_factory=list)


def quantify(flags: list, all_deals: list) -> LeakageSummary:
    """Aggregate LeakageFlag list into a LeakageSummary."""
    total_pipeline = sum((d.amount or AVG_DEAL_VALUE) for d in all_deals)

    # Dedup: per deal, take highest estimated_loss across scorers
    per_deal: dict = {}
    for flag in flags:
        cur = per_deal.get(flag.deal_id)
        flag_loss = flag.estimated_loss or 0
        if cur is None or flag_loss > (cur.estimated_loss or 0):
            per_deal[flag.deal_id] = flag

    total_leakage = sum((f.estimated_loss or 0) for f in per_deal.values())
    leakage_pct = (total_leakage / total_pipeline * 100) if total_pipeline else 0

    by_scorer: dict = {}
    by_stage: dict = {}
    for flag in flags:
        by_scorer.setdefault(flag.scorer_name, 0)
        by_scorer[flag.scorer_name] += flag.estimated_loss or 0
        by_stage.setdefault(flag.stage_label, 0)
        by_stage[flag.stage_label] += flag.estimated_loss or 0

    top_flags = sorted(flags, key=lambda f: f.estimated_loss or 0, reverse=True)[:10]

    return LeakageSummary(
        total_pipeline_value=total_pipeline,
        total_estimated_leakage=total_leakage,
        leakage_pct=leakage_pct,
        deals_flagged=len(per_deal),
        total_deals=len(all_deals),
        critical_count=sum(1 for f in flags if f.severity == "critical"),
        high_count=sum(1 for f in flags if f.severity == "high"),
        medium_count=sum(1 for f in flags if f.severity == "medium"),
        by_scorer=by_scorer,
        by_stage=by_stage,
        top_flags=top_flags,
    )
