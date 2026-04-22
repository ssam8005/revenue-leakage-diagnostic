"""
scorers/base.py — Abstract base class for all leakage signal scorers.

Each scorer accepts a list of DealRecord objects and returns LeakageFlag
objects for every deal that exhibits the signal. Callers iterate over
all scorers and aggregate flags via dollar_quantifier.py.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LeakageFlag:
    """A single scored leakage signal on a deal."""
    scorer_name: str
    deal_id: str
    deal_name: str
    stage_label: str
    severity: str            # critical | high | medium
    signal: str              # human-readable: "No activity in 34 days"
    loss_pct: float          # 0.0–1.0 probability-weighted loss
    deal_value: Optional[float]
    estimated_loss: Optional[float]
    recommendation: str


class LeakageScorer(ABC):
    """
    Base class for all leakage scorers.

    Subclasses implement score_deal(deal) → LeakageFlag | None.
    score_all() runs across all deals and returns the flagged subset.
    """

    name: str = "BaseScorer"

    def score_all(self, deals: list) -> list:
        flags = []
        for deal in deals:
            flag = self.score_deal(deal)
            if flag:
                flags.append(flag)
        return flags

    @abstractmethod
    def score_deal(self, deal) -> Optional[LeakageFlag]:
        raise NotImplementedError
