"""Normalize agent summary text and backfill diagnosis fields."""

from __future__ import annotations

import re

from app.models.incident import Incident
from app.store.protocol import DomainStore

_CONFIDENCE_RE = re.compile(
    r"confidence[^0-9%]{0,80}?(\d{1,3})\s*%",
    re.IGNORECASE | re.DOTALL,
)
_FAILURE_RE = re.compile(
    r"(?:likely\s+failure\s+mode|failure\s+mode|suspected\s+failure)"
    r"[:\s*#-]*\*?\*?\s*([^\n*#]+)",
    re.IGNORECASE,
)
_REASONING_RE = re.compile(
    r"(?:\*\*)?reasoning(?:\*\*)?\s*[:\-–]\s*(.+?)(?="
    r"\n\s*(?:#{1,4}\s|\*\*[A-Z]|\d+\.\s+[A-Z]|Actions?\s+Taken|\Z))",
    re.IGNORECASE | re.DOTALL,
)
_LATEX_INLINE_RE = re.compile(r"\$([^$]+)\$")
_LATEX_TEXT_RE = re.compile(r"\\(?:text|mathrm|textrm|mathbf)\{([^}]*)\}")


def _latex_chunk_to_plain(inner: str) -> str:
    plain = inner
    plain = plain.replace(r"\circ", "°")
    plain = plain.replace(r"\times", "x")
    plain = plain.replace(r"\,", " ")
    plain = plain.replace(r"\;", " ")
    plain = plain.replace(r"\ ", " ")
    plain = _LATEX_TEXT_RE.sub(r"\1", plain)
    plain = plain.replace("{", "").replace("}", "")
    plain = plain.replace("\\", "")
    plain = re.sub(r"\^\s*°", "°", plain)
    plain = re.sub(r"\^\s*C\b", " C", plain)
    return re.sub(r"\s+", " ", plain).strip()


def sanitize_agent_text(text: str) -> str:
    """Convert common LaTeX snippets to readable plain text."""
    if not text:
        return text
    cleaned = _LATEX_INLINE_RE.sub(
        lambda m: _latex_chunk_to_plain(m.group(1)),
        text,
    )
    cleaned = _LATEX_TEXT_RE.sub(r"\1", cleaned)
    cleaned = cleaned.replace(r"\circ", "°")
    cleaned = re.sub(r"\^\s*°", "°", cleaned)
    cleaned = re.sub(r"\^\s*C\b", " C", cleaned)
    return cleaned


def _parse_confidence(summary: str) -> float | None:
    match = _CONFIDENCE_RE.search(summary)
    if not match:
        return None
    pct = int(match.group(1))
    if pct < 0 or pct > 100:
        return None
    return round(pct / 100.0, 2)


def _parse_failure(summary: str) -> str | None:
    match = _FAILURE_RE.search(summary)
    if not match:
        return None
    text = match.group(1).strip(" :-*")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 3:
        return None
    return text[:160]


def parse_reasoning(summary: str) -> str | None:
    if not summary:
        return None
    match = _REASONING_RE.search(summary)
    if not match:
        return None
    text = sanitize_agent_text(match.group(1))
    text = re.sub(r"\s+", " ", text).strip(" -*\n")
    if len(text) < 8:
        return None
    return text[:500]


def _related_work_orders(store: DomainStore, incident: Incident):
    related = []
    for work_order in store.list_work_orders():
        if work_order.incident_id == incident.incident_id:
            related.append(work_order)
        elif (
            work_order.machine_id == incident.machine_id
            and work_order.status.value in {"OPEN", "IN_PROGRESS"}
        ):
            related.append(work_order)
    return related


def enrich_incident_diagnosis(store: DomainStore, incident: Incident) -> Incident:
    """Sanitize summary and fill suspected_failure / confidence when blank."""
    changed = False
    summary = incident.agent_summary or ""

    if summary:
        cleaned = sanitize_agent_text(summary)
        if cleaned != summary:
            incident.agent_summary = cleaned
            summary = cleaned
            changed = True

    if not incident.suspected_failure:
        for work_order in _related_work_orders(store, incident):
            if work_order.suspected_failure:
                incident.suspected_failure = work_order.suspected_failure
                changed = True
                break
        if not incident.suspected_failure and summary:
            parsed = _parse_failure(summary)
            if parsed:
                incident.suspected_failure = parsed
                changed = True

    if incident.confidence is None and summary:
        parsed_conf = _parse_confidence(summary)
        if parsed_conf is not None:
            incident.confidence = parsed_conf
            changed = True

    if changed:
        store.add_incident(incident)

    return incident
