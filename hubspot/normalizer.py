"""
hubspot/normalizer.py — Converts mock/demo JSON to DealRecord objects.

Used by --demo mode so the diagnostic runs without a HubSpot API key.
"""
import json
from pathlib import Path
from hubspot.client import DealRecord


def load_mock_deals(path: str = None) -> list:
    """Load DealRecord objects from mock JSON file."""
    if path is None:
        path = Path(__file__).parent.parent / "sample_data" / "mock_hubspot_response.json"
    with open(path) as f:
        raw = json.load(f)
    deals = []
    for d in raw:
        deals.append(DealRecord(**d))
    return deals
