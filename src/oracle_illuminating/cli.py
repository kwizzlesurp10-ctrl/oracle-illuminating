"""
Command-line entrypoints for Oracle Illuminating workflows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from oracle_illuminating.analytics import get_insight_recorder
from oracle_illuminating.workflows import illumination_cycle

app = typer.Typer(help="Oracle Illuminating agentic workflows.")


def _load_payload(payload: Optional[str], payload_path: Optional[Path]) -> dict:
    if payload and payload_path:
        raise typer.BadParameter("Provide either --payload or --payload-file, not both.")

    if payload_path:
        try:
            data = json.loads(payload_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise typer.BadParameter(f"Payload file not found: {payload_path}") from exc
    elif payload:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(f"Invalid JSON payload: {exc}") from exc
    else:
        data = {}
    return data


@app.command()
def cycle(
    payload: Optional[str] = typer.Option(
        None,
        "--payload",
        "-p",
        help="Inline JSON payload to illuminate.",
    ),
    payload_file: Optional[Path] = typer.Option(
        None,
        "--payload-file",
        "-f",
        exists=False,
        help="Path to a JSON file containing the payload.",
    ),
) -> None:
    """
    Execute a single illumination cycle via the Prefect workflow.
    """
    payload_data = _load_payload(payload, payload_file)
    result = illumination_cycle(payload=payload_data)
    typer.echo(json.dumps(result, indent=2))


@app.command("analytics")
def analytics_summary(limit: int = typer.Option(10, help="Number of recent runs to include.")) -> None:
    """
    Display analytics summaries for downstream visualization feeds.
    """
    recorder = get_insight_recorder()
    summary = {
        "oracles": recorder.oracle_acuity_summary(),
        "guardrails": recorder.guardrail_status_distribution(),
        "recent_runs": recorder.recent_runs(limit=limit),
    }
    typer.echo(json.dumps(summary, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()

