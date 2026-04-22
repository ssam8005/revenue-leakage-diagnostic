"""
Missing Enrichment Scorer — flags deals with incomplete contact data.

Missing phone, LinkedIn, or company name reduces outreach quality
and indicates the deal was never properly qualified.
"""
from typing import Optional
from config import LOSS_WEIGHTS
from scorers.base import LeakageScorer, LeakageFlag


class MissingEnrichmentScorer(LeakageScorer):
    name = "missing_enrichment"

    def score_deal(self, deal) -> Optional[LeakageFlag]:
        missing = []
        if not deal.has_contact:
            missing.append("no associated contact")
        if not deal.contact_has_phone:
            missing.append("no phone")
        if not deal.contact_has_linkedin:
            missing.append("no LinkedIn")
        if not deal.company_name:
            missing.append("no company")

        if not missing:
            return None

        severity = "critical" if len(missing) >= 3 else ("high" if len(missing) >= 2 else "medium")
        loss_pct = LOSS_WEIGHTS["missing_enrichment"][severity]
        est = (deal.amount or 0) * loss_pct if deal.amount else None

        return LeakageFlag(
            scorer_name=self.name,
            deal_id=deal.deal_id,
            deal_name=deal.deal_name,
            stage_label=deal.stage_label,
            severity=severity,
            signal=f"Missing enrichment: {', '.join(missing)}",
            loss_pct=loss_pct,
            deal_value=deal.amount,
            estimated_loss=est,
            recommendation="Run Clay enrichment or Apollo lookup to fill gaps before next outreach.",
        )
