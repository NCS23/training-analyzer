"""Tests for chat system prompt — ensures KI is instructed to use run_details (#761)."""

from datetime import date

from app.services.chat_context_service import _assemble_prompt


def test_prompt_lists_propose_week_rewrite_in_tool_overview() -> None:
    """Tool-Liste enthaelt das neue Wochen-Rewrite-Tool."""
    prompt = _assemble_prompt(date(2026, 5, 4))
    assert "propose_week_rewrite" in prompt


def test_prompt_instructs_ki_to_use_run_details_with_intervals() -> None:
    """Plan-Vorschlag-Sektion sagt KI explizit, run_details + intervals zu nutzen."""
    prompt = _assemble_prompt(date(2026, 5, 4))
    assert "run_details" in prompt
    assert "intervals" in prompt
    # Bias-buster: die alte 'Notes nur Kommentare'-Regel darf nicht so klingen,
    # als duerfe die KI in propose_plan_change keine Struktur ausspielen.
    assert "in run_details/intervals" in prompt


def test_prompt_contains_concrete_intervals_example() -> None:
    """Konkretes Beispiel zeigt der KI die erwartete Struktur."""
    prompt = _assemble_prompt(date(2026, 5, 4))
    assert "warmup" in prompt
    assert "recovery_jog" in prompt
    assert "target_pace_min" in prompt


def test_prompt_warns_against_hiding_structure_in_notes() -> None:
    """Prompt enthaelt explizite Warnung: Struktur NICHT in notes verstecken."""
    prompt = _assemble_prompt(date(2026, 5, 4))
    # Die Warnung muss im Prompt stehen — sowohl in der Plan-Vorschlag-Sektion
    # als auch in der Plan-Erstellungs-Sektion.
    assert "NICHT die Struktur in `notes`" in prompt or "niemals nur in notes" in prompt
