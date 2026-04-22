"""
No Next Step Scorer — flags deals with no task or overdue close date.

Missing next step is the #1 predictor of deal loss in B2B pipelines.
Loss weight: 42% (high) — source: HubSpot Pipeline Benchmark Report 2024.
"""
from typing import Optional
from config import LOSS_WEIGHTS
from scorers.base import LeakageScorer, LeakageFlag


class NoNextStepScorer(LeakageScorer):
    name = "no_next_step"

    def score_deal(self, deal) -> Optional[LeakageFlag]:
        signals = []
        if not deal.has_next_step:
            signals.append("no next step set")
        if deal.close_date_passed:
            signals.append("close date overdue")

        if not signals:
            return None

        severity = "critical" if len(signals) == 2 else "high"
        loss_pct = LOSS_WEIGHTS["no_next_step"][severity]
        est = (deal.amount or 0) * loss_pct if deal.amount else None

        return LeakageFlag(
            scorer_name=self.name,
            deal_id=deal.deal_id,
            deal_name=deal.deal_name,
            stage_label=deal.stage_label,
            severity=severity,
            signal=f"No clear path forward: {', '.join(signals)}",
            loss_pct=loss_pct,
            deal_value=deal.amount,
            estimated_loss=est,
            recommendation="Set a specific next step with a date. Update close date to reflect reality.",
        )
