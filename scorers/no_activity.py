"""
No Activity Scorer — flags deals with no logged engagement.

No email, call, or note in N days signals a deal going cold.
Loss weight: 28% (high) — source: Gong Revenue Intelligence 2024.
"""
from typing import Optional
from config import NO_ACTIVITY_DAYS, LOSS_WEIGHTS
from scorers.base import LeakageScorer, LeakageFlag


class NoActivityScorer(LeakageScorer):
    name = "no_activity"

    THRESHOLDS = {"critical": 30, "high": NO_ACTIVITY_DAYS, "medium": 7}

    def score_deal(self, deal) -> Optional[LeakageFlag]:
        days = deal.last_activity_days_ago
        severity = None
        for level in ("critical", "high", "medium"):
            if days >= self.THRESHOLDS[level]:
                severity = level
                break
        if not severity:
            return None

        loss_pct = LOSS_WEIGHTS["no_activity"][severity]
        est = (deal.amount or 0) * loss_pct if deal.amount else None

        return LeakageFlag(
            scorer_name=self.name,
            deal_id=deal.deal_id,
            deal_name=deal.deal_name,
            stage_label=deal.stage_label,
            severity=severity,
            signal=f"No logged activity for {days} days",
            loss_pct=loss_pct,
            deal_value=deal.amount,
            estimated_loss=est,
            recommendation="Log a touchpoint or send a break-up email to re-engage or disqualify.",
        )
