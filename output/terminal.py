"""
output/terminal.py — Rich terminal output for the leakage diagnostic.

Color coding: critical = red, high = yellow, medium = orange.
Final line: bold "Estimated Revenue at Risk: $X"
"""
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from analysis.dollar_quantifier import LeakageSummary

console = Console()

SEVERITY_COLORS = {"critical": "bold red", "high": "yellow", "medium": "dark_orange"}


def print_summary(summary: LeakageSummary, ai_result: dict):
    console.print()
    console.rule("[bold blue]Revenue Leakage Diagnostic — Results[/bold blue]")
    console.print()

    # AI executive summary
    if ai_result.get("executive_summary"):
        console.print(f"[italic]{ai_result['executive_summary']}[/italic]")
        console.print()

    # Pipeline score
    score = ai_result.get("pipeline_score", 0)
    score_color = "green" if score >= 75 else ("yellow" if score >= 50 else "red")
    console.print(f"Pipeline Health Score: [{score_color}]{score}/100[/{score_color}]")
    console.print()

    # Summary stats
    stats = Table(box=box.SIMPLE, show_header=False)
    stats.add_row("Total pipeline scanned", f"${summary.total_pipeline_value:,.0f}")
    stats.add_row("[bold red]Estimated revenue at risk[/bold red]", f"[bold red]${summary.total_estimated_leakage:,.0f}[/bold red]")
    stats.add_row("Leakage %", f"{summary.leakage_pct:.1f}%")
    stats.add_row("Deals flagged", f"{summary.deals_flagged} of {summary.total_deals}")
    stats.add_row("Critical flags", str(summary.critical_count))
    stats.add_row("High flags", str(summary.high_count))
    stats.add_row("Medium flags", str(summary.medium_count))
    console.print(stats)

    # Top flags table
    console.rule("[bold]Top Leakage Signals[/bold]")
    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Severity", style="bold", width=10)
    table.add_column("Deal", width=28)
    table.add_column("Stage", width=22)
    table.add_column("Signal", width=36)
    table.add_column("Est. Loss", justify="right", width=12)
    table.add_column("Action", width=38)

    for flag in summary.top_flags:
        color = SEVERITY_COLORS.get(flag.severity, "white")
        est = f"${flag.estimated_loss:,.0f}" if flag.estimated_loss else "—"
        table.add_row(
            Text(flag.severity.upper(), style=color),
            flag.deal_name[:26],
            flag.stage_label[:20],
            flag.signal[:34],
            est,
            flag.recommendation[:36],
        )
    console.print(table)

    # Top actions
    actions = ai_result.get("top_actions", [])
    if actions:
        console.rule("[bold green]Priority Actions[/bold green]")
        for a in actions:
            console.print(f"  {a['priority']}. {a['action']} — [green]{a['estimated_recovery']} recovery[/green]")
        console.print()

    console.print(
        f"[bold red]  Estimated Total Revenue at Risk: ${summary.total_estimated_leakage:,.0f}[/bold red]"
    )
    console.print()
