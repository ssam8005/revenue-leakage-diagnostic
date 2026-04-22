"""
Stuck Deal Scorer — flags deals stagnant in the same pipeline stage.

Severity thresholds:
    critical > 45 days  (55% loss weight)
    high     > 21 days  (35% loss weight — default STUCK_DEAL_DAYS)
    medium   > 14 days  (15% early warning)

Source: Salesforce State of Sales Report 2024 — deals stuck >21d in stage
close at 35% of the rate of actively-progressing deals.
"""
from typing import Optional
from config import STUCK_DEAL_DAYS, LOSS_WEIGHTS
from scorers.base import LeakageScorer, LeakageFlag


class StuckDealScorer(LeakageScorer):
    name = "stuck_deal"

    THRESHOLDS = {"critical": 45, "high": STUCK_DEAL_DAYS, "medium": 14}

    def score_deal(self, deal) -> Optional[LeakageFlag]:
        days = deal.days_in_stage
        severity = None
        for level in ("critical", "high", "medium"):
            if days >= self.THRESHOLDS[level]:
                severity = level
                break
        if not severity:
            return None

        loss_pct = LOSS_WEIGHTS["stuck_deal"][severity]
        est = (deal.amount or 0) * loss_pct if deal.amount else None

        return LeakageFlag(
            scorer_name=self.name,
            deal_id=deal.deal_id,
            deal_name=deal.deal_name,
            stage_label=deal.stage_label,
            severity=severity,
            signal=f"Stagnant in '{deal.stage_label}' for {days} days",
            loss_pct=loss_pct,
            deal_value=deal.amount,
            estimated_loss=est,
            recommendation=(
                f"Schedule call or mark lost within 48 hrs. "
                f"Deals stuck >{self.THRESHOLDS['high']}d close at 35% of normal rate."
            ),
        )
