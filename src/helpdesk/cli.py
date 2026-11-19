from __future__ import annotations

import asyncio
import sys

import typer

from .config import load_tenant

app = typer.Typer(add_completion=False, help="White-label HR/IT helpdesk agent")


@app.command()
def ask(
    question: str = typer.Argument(..., help="The employee's question"),
    as_: str = typer.Option("E102", "--as", help="Employee id the question is asked as"),
    verbose: bool = typer.Option(True, "--verbose/--quiet"),
) -> None:
    """Ask the helpdesk agent a question."""
    from .agent import ask as run

    t = load_tenant()
    res = asyncio.run(run(question, as_))
    typer.echo(f"\n[{t.assistant_name} @ {t.company_name}]\n{res.answer}\n")
    if verbose:
        typer.echo(f"  verdict : {res.verdict['kind']} ({res.verdict['layer']}) - {res.verdict['reason']}")
        typer.echo(f"  tools   : {', '.join(res.tools_called) or '-'}")
        typer.echo(f"  sources : {'; '.join(res.sources) or '-'}")
        if res.output_actions:
            typer.echo(f"  output  : {', '.join(res.output_actions)}")
        cost = f", ~${res.cost_usd:.5f}" if res.cost_usd is not None else ""
        typer.echo(f"  latency : {res.latency_s:.1f}s, {res.input_tokens}+{res.output_tokens} tokens{cost}")


@app.command()
def info() -> None:
    """Show the active tenant configuration."""
    t = load_tenant()
    typer.echo(f"{t.assistant_name} for {t.company_name} (tone: {t.tone})")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    app()
