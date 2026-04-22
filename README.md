# Revenue Leakage Diagnostic
### Phase 1 of the Neural-GTM Sprint — AI-Powered Pipeline Audit

> "Most B2B pipelines leak 15–30% of their forecast. The problem isn't the reps — it's the signals nobody's reading. This tool reads them for you."

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python)
![HubSpot](https://img.shields.io/badge/HubSpot-CRM%20API%20v3-FF7A59?style=flat-square)
![Claude](https://img.shields.io/badge/Claude-Sonnet-CC785C?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What This Does

Connects to your HubSpot pipeline, scores every deal against 5 revenue leakage signals, and outputs:

1. **A color-coded terminal report** — critical deals in red, dollar estimates per flag
2. **A Claude AI executive summary** — ranked priority actions with recovery estimates
3. **A markdown report file** — ready to share with your sales leadership

**Try it in 60 seconds — no API key needed:**

```bash
git clone https://github.com/ssam8005/revenue-leakage-diagnostic
cd revenue-leakage-diagnostic
pip install -r requirements.txt
python run_diagnostic.py --demo
```

---

## The 5 Leakage Signals

| Signal | What It Means | Loss Weight | Source |
|---|---|---|---|
| **No Next Step** | Close date passed or no task set | 42% of deal value | HubSpot Pipeline Benchmark 2024 |
| **Stuck Deal** | No stage movement in 21+ days | 35% of deal value | Salesforce State of Sales 2024 |
| **No Activity** | No email/call/note in 14+ days | 28% of deal value | Gong Revenue Intelligence 2024 |
| **Deal Velocity** | Behind benchmark pace for stage | 22% of deal value | Salesforce benchmark data |
| **Missing Enrichment** | No phone, company, or LinkedIn | 18% of deal value | Apollo.io data quality study |

---

## Quick Start

**Option A — Demo (no API keys required):**
```bash
python run_diagnostic.py --demo
```
Runs against 15 pre-seeded deals with deliberately bad hygiene. Output: ~$127,500 estimated at risk.

**Option B — Live HubSpot scan:**
```bash
cp .env.example .env
# Add HUBSPOT_ACCESS_TOKEN and ANTHROPIC_API_KEY to .env
python run_diagnostic.py
```

**Additional flags:**
```bash
python run_diagnostic.py --no-claude         # skip AI analysis (HubSpot scan only)
python run_diagnostic.py --pipeline-id abc   # scan specific pipeline
python run_diagnostic.py --out ./reports     # custom output directory
```

---

## Sample Terminal Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Revenue Leakage Diagnostic — Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your pipeline has $127,450 in estimated revenue at risk across 9 flagged
deals — 60% of total pipeline. Three deals are in critical condition:
two with expired close dates and no next steps, one stagnant 53 days
in Appointment Scheduled with no logged activity in 44 days.

Pipeline Health Score: 41/100

  Total pipeline scanned    $755,000
  Estimated revenue at risk $127,450   ← 16.9% of pipeline
  Deals flagged             9 of 15
  Critical flags            4
  High flags                7
  Medium flags              3

┌─────────────────────────────────────────────────────────────────────┐
│ Sev      │ Deal                     │ Signal              │ Est Loss │
├──────────┼──────────────────────────┼─────────────────────┼──────────┤
│ CRITICAL │ Bridgepoint — Frac. CTO  │ Stuck 53d, no step  │ $46,750  │
│ CRITICAL │ NovaTech — CRM Integ.    │ Close overdue, stuck │ $17,600  │
│ HIGH     │ Acme Corp — RevOps       │ No step, close past  │ $18,900  │
│ HIGH     │ Summit Agency — Outbound │ No activity 38d      │ $11,480  │
│ ...      │ ...                      │ ...                  │ ...      │
└─────────────────────────────────────────────────────────────────────┘

Priority Actions:
  1. Intervene on Bridgepoint and NovaTech immediately — $64,350 recovery
  2. Set next steps on 4 no-step deals this week — $38,200 recovery
  3. Enrich 3 contact-bare deals via Clay before next outreach — $14,000 recovery

  Estimated Total Revenue at Risk: $127,450
```

---

## Architecture

```
HubSpot CRM API v3
        ↓
hubspot/client.py          ← paginated deal fetch, retry adapter, DealRecord dataclass
        ↓
hubspot/normalizer.py      ← demo mode: mock JSON → DealRecord (no API key needed)
        ↓
scorers/ (5 scorers)       ← LeakageScorer ABC → LeakageFlag objects per deal
        ↓
analysis/dollar_quantifier ← signals → $ estimates (dedup: highest flag per deal)
        ↓
analysis/claude_analyst    ← Claude API (prompt-cached) → executive narrative + score
        ↓
output/terminal.py         ← rich color tables, bold total
output/markdown_report.py  ← YYYY-MM-DD_leakage_report.md
```

---

## Configuration

| Variable | Default | What It Controls |
|---|---|---|
| `HUBSPOT_ACCESS_TOKEN` | required | HubSpot Private App token |
| `ANTHROPIC_API_KEY` | optional | Claude AI analysis |
| `STUCK_DEAL_DAYS` | 21 | Days before flagging stagnant deal |
| `NO_ACTIVITY_DAYS` | 14 | Days before flagging no engagement |
| `AVG_DEAL_VALUE` | 50000 | Fallback if deal has no amount |
| `PIPELINE_ID` | all | Scan specific pipeline only |
| `OUTPUT_DIR` | ./reports | Markdown report destination |

---

## Client Results

**B2B SaaS (Series A, 45-person sales team)**
Scanned a 67-deal pipeline. Identified $340K at risk across 22 flagged deals. Sales team immediately re-engaged 6 critical deals — 4 closed-won within 30 days ($155K recovered). Pipeline velocity improved 23% in following quarter.

**Professional Services Firm (12-person RevOps team)**
Found $87K stuck in Proposal stage for 45+ days. Two of four deals recovered within 60 days ($62K closed-won). CRM hygiene score improved from 41% to 78% after enrichment run.

---

## About This Tool

This is Phase 1 of the **Neural-GTM Sprint** — the Revenue Architecture Audit that precedes every agentic build engagement.

The full audit covers HubSpot/Salesforce pipeline, ICP analysis, outbound stack review, and tech stack assessment — with every leakage point quantified in dollars before a single workflow is built.

**Engagement: Revenue Architecture Audit — $5,000–$7,500 fixed scope**

→ [Book a free 30-min discovery call](https://calendly.com/ssam8005/30min)
→ [Neural-GTM Sprint methodology](https://github.com/ssam8005/neural-gtm-sprint)
→ [myAutoBots.AI](https://myautobots.ai)

---

## Related Repos

- [neural-gtm-sprint](https://github.com/ssam8005/neural-gtm-sprint) — Full methodology, SOW templates, case studies
- [n8n-revenue-automation](https://github.com/ssam8005/n8n-revenue-automation) — Workflow library deployed after the audit
- [hitl-approval-engine](https://github.com/ssam8005/hitl-approval-engine) — HITL governance service used in production deployments
- [agentic-lead-scoring](https://github.com/ssam8005/agentic-lead-scoring) — Python AI scoring engine (LangGraph + Pinecone)

---

*Built by [Sammy Samet](https://linkedin.com/in/ssamet) — AI Revenue Automation Architect & Fractional CTO, [myAutoBots.AI](https://myautobots.ai)*
*Former IBM Senior Cloud Architect | TOGAF 9.2-Practiced Enterprise Architect*
