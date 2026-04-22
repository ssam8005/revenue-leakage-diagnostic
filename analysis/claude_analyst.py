"""
analysis/claude_analyst.py — Claude AI narrative synthesis layer.

Synthesizes structured leakage data into an executive-readable report:
    - executive_summary (3–5 sentences, dollar-led)
    - top_actions (3 ranked recommendations with recovery estimates)
    - pipeline_score (0–100, lower = more leakage)
    - bottleneck_narrative (worst stage in one sentence)

Uses claude-sonnet-4-6 with prompt caching on the static system prompt
to reduce token cost ~60% on large pipeline scans.

Cost: ~$0.02–$0.08 per diagnostic run depending on pipeline size.
"""
import json
import logging
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from analysis.dollar_quantifier import LeakageSummary

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Revenue Operations analyst with 20+ years of B2B sales experience.
You receive structured data about a company's CRM pipeline — specifically deals flagged for
revenue leakage signals (stuck stages, missing enrichment, no activity, no next step, velocity lag).

Your job: synthesize this into a crisp, dollar-focused executive report.

Rules:
- Lead with the total estimated dollar leakage — not percentages
- Rank recommendations by estimated revenue recovery impact, highest first
- Use plain language — assume the reader is a VP of Sales, not a developer
- Use direct language: "critical", "urgent", "watch list" — not soft hedging
- Reference specific stage names or deal patterns when making recommendations
- Respond in valid JSON only — no markdown fences, no extra text
"""


class ClaudeAnalyst:
    """Calls Claude API to generate the AI narrative section."""

    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.available = True
        except Exception as exc:
            logger.warning(f"Claude not available: {exc}")
            self.available = False

    def synthesize(self, summary: LeakageSummary, flags: list) -> dict:
        """
        Generate executive narrative from LeakageSummary + flag list.

        Returns dict with keys: executive_summary, top_actions, pipeline_score,
        bottleneck_narrative. Falls back to rule-based summary if Claude unavailable.
        """
        if not self.available or not ANTHROPIC_API_KEY:
            return self._fallback(summary)

        flags_data = [
            {
                "deal": f.deal_name,
                "stage": f.stage_label,
                "severity": f.severity,
                "signal": f.signal,
                "estimated_loss": round(f.estimated_loss or 0, 2),
                "recommendation": f.recommendation,
            }
            for f in flags[:30]  # cap at 30 flags for token efficiency
        ]

        user_prompt = f"""Pipeline Leakage Report Data
===========================
Total pipeline scanned: ${summary.total_pipeline_value:,.0f}
Total estimated leakage: ${summary.total_estimated_leakage:,.0f} ({summary.leakage_pct:.1f}%)
Deals flagged: {summary.deals_flagged} of {summary.total_deals}
Critical: {summary.critical_count} | High: {summary.high_count} | Medium: {summary.medium_count}

Worst stages by leakage:
{json.dumps(summary.by_stage, indent=2)}

Top flags (JSON):
{json.dumps(flags_data, indent=2)}

Return JSON with exactly these keys:
{{
  "executive_summary": "3-5 sentences, leads with dollar figure",
  "top_actions": [
    {{"action": "...", "estimated_recovery": "$X", "priority": 1}},
    {{"action": "...", "estimated_recovery": "$X", "priority": 2}},
    {{"action": "...", "estimated_recovery": "$X", "priority": 3}}
  ],
  "pipeline_score": 0-100,
  "bottleneck_narrative": "one sentence on worst stage"
}}
"""

        try:
            import anthropic
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=[{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # prompt caching on static system prompt
                }],
                messages=[{"role": "user", "content": user_prompt}],
            )
            return json.loads(response.content[0].text)
        except Exception as exc:
            logger.error(f"Claude synthesis failed: {exc}")
            return self._fallback(summary)

    def _fallback(self, summary: LeakageSummary) -> dict:
        """Rule-based fallback when Claude API is unavailable."""
        score = max(0, 100 - int(summary.leakage_pct * 2))
        worst_stage = max(summary.by_stage, key=summary.by_stage.get) if summary.by_stage else "unknown"
        return {
            "executive_summary": (
                f"Pipeline scan identified ${summary.total_estimated_leakage:,.0f} in estimated revenue at risk "
                f"across {summary.deals_flagged} of {summary.total_deals} deals ({summary.leakage_pct:.1f}% of pipeline). "
                f"{summary.critical_count} deals are in critical condition requiring immediate action."
            ),
            "top_actions": [
                {"action": "Address critical-severity deals immediately", "estimated_recovery": f"${summary.total_estimated_leakage * 0.4:,.0f}", "priority": 1},
                {"action": f"Clear bottleneck in '{worst_stage}' stage", "estimated_recovery": f"${summary.by_stage.get(worst_stage, 0):,.0f}", "priority": 2},
                {"action": "Run enrichment on deals missing contact data", "estimated_recovery": f"${summary.by_scorer.get('missing_enrichment', 0):,.0f}", "priority": 3},
            ],
            "pipeline_score": score,
            "bottleneck_narrative": f"'{worst_stage}' stage accounts for the highest estimated leakage.",
        }
