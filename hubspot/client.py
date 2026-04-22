"""
hubspot/client.py — HubSpot CRM API v3 wrapper.

Fetches all deals with associated contacts and engagement history.
Handles pagination, rate limiting (429 retry), and normalization.
Callers receive a flat list of DealRecord objects — no API details leak out.
"""
import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://api.hubapi.com"

DEAL_PROPERTIES = [
    "dealname", "pipeline", "dealstage", "amount", "closedate",
    "createdate", "hs_lastmodifieddate", "hubspot_owner_id",
    "hs_next_step", "notes_last_contacted", "hs_date_entered_dealstage",
    "hs_num_associated_contacts", "company",
]


@dataclass
class DealRecord:
    """Normalized HubSpot deal — clean internal model passed to all scorers."""
    deal_id: str
    deal_name: str
    pipeline_id: str
    stage_id: str
    stage_label: str
    amount: Optional[float]
    close_date: Optional[str]
    create_date: str
    days_in_stage: int
    last_activity_days_ago: int
    has_contact: bool
    contact_has_phone: bool
    contact_has_linkedin: bool
    company_name: Optional[str]
    has_next_step: bool
    close_date_passed: bool
    engagement_count: int
    owner_id: Optional[str]


class HubSpotClient:
    """
    Thin wrapper around HubSpot CRM API v3.

    Args:
        access_token: Private App token from HubSpot Settings → Integrations.
        pipeline_id:  If set, filters to that pipeline only.
    """

    PAGE_SIZE = 100

    def __init__(self, access_token: str, pipeline_id: str = ""):
        self.token = access_token
        self.pipeline_id = pipeline_id
        self.session = self._build_session()
        self._stage_label_cache: dict = {}

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.headers.update({"Authorization": f"Bearer {self.token}"})
        return session

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{BASE_URL}{path}"
        r = self.session.get(url, params=params or {})
        r.raise_for_status()
        return r.json()

    def _fetch_stage_labels(self) -> dict:
        """Cache pipeline stage ID → label mapping."""
        if self._stage_label_cache:
            return self._stage_label_cache
        try:
            data = self._get("/crm/v3/pipelines/deals")
            for pipeline in data.get("results", []):
                for stage in pipeline.get("stages", []):
                    self._stage_label_cache[stage["id"]] = stage["label"]
        except Exception as exc:
            logger.warning(f"Could not fetch stage labels: {exc}")
        return self._stage_label_cache

    def _days_since(self, iso_date: Optional[str]) -> int:
        if not iso_date:
            return 999
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - dt
            return max(0, delta.days)
        except Exception:
            return 999

    def _close_date_passed(self, close_date: Optional[str]) -> bool:
        if not close_date:
            return False
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(close_date.replace("Z", "+00:00"))
            return dt < datetime.now(timezone.utc)
        except Exception:
            return False

    def fetch_all_deals(self) -> list:
        """Paginate all deals and return normalized DealRecord list."""
        stage_labels = self._fetch_stage_labels()
        deals = []
        after = None

        while True:
            params = {
                "limit": self.PAGE_SIZE,
                "properties": ",".join(DEAL_PROPERTIES),
                "associations": "contacts",
            }
            if after:
                params["after"] = after
            if self.pipeline_id:
                params["filterGroups"] = []

            data = self._get("/crm/v3/objects/deals", params)
            results = data.get("results", [])

            for raw in results:
                props = raw.get("properties", {})
                stage_id = props.get("dealstage", "")
                pipeline_id = props.get("pipeline", "")

                if self.pipeline_id and pipeline_id != self.pipeline_id:
                    continue

                # Engagement count (cheap proxy via associations)
                eng_count = 0
                try:
                    eng_data = self._get(
                        f"/crm/v3/objects/deals/{raw['id']}/associations/engagements"
                    )
                    eng_count = len(eng_data.get("results", []))
                except Exception:
                    pass

                # Contact details
                has_contact = False
                has_phone = False
                has_linkedin = False
                assoc = raw.get("associations", {}).get("contacts", {})
                contact_ids = [c["id"] for c in assoc.get("results", [])]
                if contact_ids:
                    has_contact = True
                    try:
                        c_data = self._get(
                            f"/crm/v3/objects/contacts/{contact_ids[0]}",
                            {"properties": "phone,hs_linkedin_url"}
                        )
                        cp = c_data.get("properties", {})
                        has_phone = bool(cp.get("phone"))
                        has_linkedin = bool(cp.get("hs_linkedin_url"))
                    except Exception:
                        pass

                amount = None
                try:
                    amount = float(props.get("amount") or 0) or None
                except Exception:
                    pass

                record = DealRecord(
                    deal_id=raw["id"],
                    deal_name=props.get("dealname", "Unnamed Deal"),
                    pipeline_id=pipeline_id,
                    stage_id=stage_id,
                    stage_label=stage_labels.get(stage_id, stage_id),
                    amount=amount,
                    close_date=props.get("closedate"),
                    create_date=props.get("createdate", ""),
                    days_in_stage=self._days_since(props.get("hs_date_entered_dealstage")),
                    last_activity_days_ago=self._days_since(props.get("notes_last_contacted")),
                    has_contact=has_contact,
                    contact_has_phone=has_phone,
                    contact_has_linkedin=has_linkedin,
                    company_name=props.get("company"),
                    has_next_step=bool(props.get("hs_next_step")),
                    close_date_passed=self._close_date_passed(props.get("closedate")),
                    engagement_count=eng_count,
                    owner_id=props.get("hubspot_owner_id"),
                )
                deals.append(record)

            paging = data.get("paging", {})
            after = paging.get("next", {}).get("after")
            if not after:
                break

        logger.info(f"Fetched {len(deals)} deals from HubSpot")
        return deals
