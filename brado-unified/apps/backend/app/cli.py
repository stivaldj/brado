from __future__ import annotations

from datetime import date

import typer

from .jobs.orchestrator import JobOrchestrator
from .political_interview.service import InterviewService

app = typer.Typer(help="BRADO data-core CLI")


def _parse_date(from_value: str) -> date:
    return date.fromisoformat(from_value)


@app.command("ingest:all")
def ingest_all(from_value: str = typer.Option("2018-01-01", "--from")) -> None:
    result = JobOrchestrator().ingest_all(_parse_date(from_value))
    typer.echo(result)


@app.command("ingest:deputados")
def ingest_deputados() -> None:
    typer.echo(JobOrchestrator().ingest_deputados())


@app.command("ingest:bills")
def ingest_bills(from_value: str = typer.Option("2018-01-01", "--from")) -> None:
    typer.echo(JobOrchestrator().ingest_bills(_parse_date(from_value)))


@app.command("ingest:votes")
def ingest_votes(from_value: str = typer.Option("2018-01-01", "--from")) -> None:
    typer.echo(JobOrchestrator().ingest_votes(_parse_date(from_value)))


@app.command("ingest:expenses")
def ingest_expenses(from_value: str = typer.Option("2018-01-01", "--from")) -> None:
    typer.echo(JobOrchestrator().ingest_expenses(_parse_date(from_value)))


@app.command("reconcile:all")
def reconcile_all() -> None:
    typer.echo(JobOrchestrator().reconcile_all())


@app.command("test:smoke-real")
def test_smoke_real(sample_size: int = typer.Option(5, "--sample-size")) -> None:
    typer.echo(JobOrchestrator().smoke_real(sample_size=sample_size))


@app.command("interview:seed")
def interview_seed(total: int = typer.Option(600, "--total")) -> None:
    typer.echo(InterviewService().seed_questions(total=total))


@app.command("interview:refresh-profiles")
def interview_refresh_profiles(limit_payloads: int = typer.Option(500, "--limit-payloads")) -> None:
    typer.echo(JobOrchestrator().refresh_political_profiles(limit_payloads=limit_payloads))


if __name__ == "__main__":
    app()
