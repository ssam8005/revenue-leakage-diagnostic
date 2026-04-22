"""
config.py — Centralized thresholds and scoring weights.

All tunable parameters live here. Modify per client without touching scorer logic.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# HubSpot
HUBSPOT_ACCESS_TOKEN: str = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
PIPELINE_ID: str = os.getenv("PIPELINE_ID", "")

# Anthropic
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = "claude-sonnet-4-6"

# Leakage signal thresholds
STUCK_DEAL_DAYS: int = int(os.getenv("STUCK_DEAL_DAYS", 21))
NO_ACTIVITY_DAYS: int = int(os.getenv("NO_ACTIVITY_DAYS", 14))
AVG_DEAL_VALUE: float = float(os.getenv("AVG_DEAL_VALUE", 50000))

# Loss weights by signal (probability of full deal loss, per industry benchmarks)
# Sources: Salesforce State of Sales 2024, HubSpot Pipeline Benchmark Report 2024, Gong Revenue Intelligence
LOSS_WEIGHTS = {
    "no_next_step":        {"critical": 0.55, "high": 0.42, "medium": 0.20},
    "stuck_deal":          {"critical": 0.55, "high": 0.35, "medium": 0.15},
    "no_activity":         {"critical": 0.50, "high": 0.28, "medium": 0.12},
    "deal_velocity":       {"critical": 0.45, "high": 0.22, "medium": 0.10},
    "missing_enrichment":  {"critical": 0.30, "high": 0.18, "medium": 0.08},
}

# Stage velocity benchmarks (expected days per stage for B2B SaaS, <200 employees)
STAGE_VELOCITY_BENCHMARKS = {
    "appointment scheduled":  7,
    "qualified to buy":      14,
    "presentation scheduled": 7,
    "decision maker bought in": 10,
    "contract sent":          5,
    "closed won":             0,
    "default":               14,
}

# Output
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./reports")
