#!/usr/bin/env python3
"""
Revenue Leakage Diagnostic — CLI Entry Point
=============================================
Connects to HubSpot, scores your deal pipeline for revenue leakage signals,
and outputs a dollar-quantified markdown report with Claude AI analysis.

Part of the Neural-GTM Sprint — Phase 1 Revenue Architecture Audit.
© myAutoBots.AI — Sammy Samet | myautobots.ai

Usage:
    python run_diagnostic.py                      # full scan (requires .env)
    python run_diagnostic.py --demo               # run on sample data, no API key needed
    python run_diagnostic.py --no-claude          # skip AI narrative, HubSpot only
    python run_diagnostic.py --pipeline-id abc    # scan specific pipeline only
    python run_diagnostic.py --out ./my-reports   # custom output directory
"""
import argparse
import logging
import sys
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Revenue Leakage Diagnostic")
    parser.add_argument("--demo", action="store_true", help="Run against sample data (no API key needed)")
    parser.add_argument("--no-claude", action="store_true", help="Skip Claude AI analysis")
    parser.add_argument("--pipeline-id", default="", help="Scan specific HubSpot pipeline only")
    parser.add_argument("--out", default="", help="Output directory for markdown report")
    args = parser.parse_args()

    if args.out:
        import config
        config.OUTPUT_DIR = args.out

    # ── Step 1: Load deals ──────────────────────────────────────────────────────
    if args.demo:
        from hubspot.normalizer import load_mock_deals
        print("Running in --demo mode with sample data...")
        deals = load_mock_deals()
    else:
        import config
        if not config.HUBSPOT_ACCESS_TOKEN:
            print("Error: HUBSPOT_ACCESS_TOKEN not set. Add it to .env or use --demo")
            sys.exit(1)
        from hubspot.client import HubSpotClient
        print("Connecting to HubSpot...")
        client = HubSpotClient(config.HUBSPOT_ACCESS_TOKEN, pipeline_id=args.pipeline_id)
        deals = client.fetch_all_deals()

    print(f"Loaded {len(deals)} deals.")

    # ── Step 2: Run all scorers ─────────────────────────────────────────────────
    from scorers.stuck_deals import StuckDealScorer
    from scorers.no_activity import NoActivityScorer
    from scorers.missing_enrichment import MissingEnrichmentScorer
    from scorers.no_next_step import NoNextStepScorer
    from scorers.deal_velocity import DealVelocityScorer

    scorers = [
        StuckDealScorer(),
        NoActivityScorer(),
        MissingEnrichmentScorer(),
        NoNextStepScorer(),
        DealVelocityScorer(),
    ]

    all_flags = []
    for scorer in scorers:
        flags = scorer.score_all(deals)
        all_flags.extend(flags)
        print(f"  {scorer.name}: {len(flags)} flags")

    # ── Step 3: Quantify ────────────────────────────────────────────────────────
    from analysis.dollar_quantifier import quantify
    summary = quantify(all_flags, deals)

    # ── Step 4: Claude synthesis ────────────────────────────────────────────────
    ai_result = {}
    if not args.no_claude:
        from analysis.claude_analyst import ClaudeAnalyst
        print("Running Claude AI analysis...")
        analyst = ClaudeAnalyst()
        ai_result = analyst.synthesize(summary, all_flags)
    else:
        from analysis.claude_analyst import ClaudeAnalyst
        ai_result = ClaudeAnalyst()._fallback(summary)

    # ── Step 5: Output ──────────────────────────────────────────────────────────
    from output.terminal import print_summary
    print_summary(summary, ai_result)

    from output.markdown_report import write_report
    report_path = write_report(summary, ai_result, all_flags)
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
