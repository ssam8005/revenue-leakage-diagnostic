"""
Deal Velocity Scorer — flags deals running behind stage-velocity benchmarks.

Compares actual days in stage vs. expected benchmark for B2B SaaS (<200 employees).
"""
from typing import Optional
from config import LOSS_WEIGHTS, STAGE_VELOCITY_BENCHMARKS
from scorers.base import LeakageScorer, LeakageFlag


class DealVelocityScorer(LeakageScorer):
    name = "deal_velocity"

    def score_deal(self, deal) -> Optional[LeakageFlag]:
        label_lower = deal.stage_label.lower()
        benchmark = STAGE_VELOCITY_BENCHMARKS.get(label_lower, STAGE_VELOCITY_BENCHMARKS["default"])
        overage = deal.days_in_stage - benchmark

        if overage < 7:
            return None

        severity = "critical" if overage >= 21 else ("high" if overage >= 14 else "medium")
        loss_pct = LOSS_WEIGHTS["deal_velocity"][severity]
        est = (deal.amount or 0) * loss_pct if deal.amount else None

        return LeakageFlag(
            scorer_name=self.name,
            deal_id=deal.deal_id,
            deal_name=deal.deal_name,
            stage_label=deal.stage_label,
            severity=severity,
            signal=f"Behind benchmark by {overage} days (expected {benchmark}d in '{deal.stage_label}')",
            loss_pct=loss_pct,
            deal_value=deal.amount,
            estimated_loss=est,
            recommendation=f"Stage should take ~{benchmark} days. Diagnose the blocker and escalate.",
        )
