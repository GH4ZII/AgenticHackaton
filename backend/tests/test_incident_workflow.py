"""Incident workflow tests (agent mocked / disabled)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.incident import IncidentStatus
from app.services.agent_runner import AgentRunResult
from app.services.incident_workflow import handle_telemetry
from tests.conftest import make_sample


@pytest.mark.asyncio
async def test_healthy_sample_skips_agent(store):
    result = await handle_telemetry(store, make_sample())
    assert result.anomaly.is_anomalous is False
    assert result.agent_invoked is False
    assert result.incident is None


@pytest.mark.asyncio
async def test_new_anomaly_with_agent_disabled(store):
    result = await handle_telemetry(
        store,
        make_sample(temperature_c=86.0),
        invoke_agent=False,
    )
    assert result.anomaly.created is True
    assert result.agent_invoked is False
    assert result.agent_skipped_reason == "invoke_agent_disabled"
    assert result.incident is not None
    assert result.incident.status == IncidentStatus.OPEN


@pytest.mark.asyncio
async def test_duplicate_skips_agent(store):
    first = await handle_telemetry(
        store,
        make_sample(temperature_c=86.0),
        invoke_agent=False,
    )
    assert first.anomaly.created is True

    second = await handle_telemetry(
        store,
        make_sample(temperature_c=90.0),
        invoke_agent=True,
    )
    assert second.agent_invoked is False
    assert second.agent_skipped_reason == "open_incident_already_exists"
    assert second.incident is not None
    assert first.incident is not None
    assert second.incident.incident_id == first.incident.incident_id


@pytest.mark.asyncio
async def test_new_incident_invokes_mocked_agent(store):
    mock_result = AgentRunResult(
        prompt="test",
        tool_calls=["get_machine_context", "create_work_order"],
        final_text="Bearing degradation diagnosed.",
    )
    with patch(
        "app.services.incident_workflow.run_maintenance_agent",
        new=AsyncMock(return_value=mock_result),
    ) as mock_agent:
        result = await handle_telemetry(
            store,
            make_sample(temperature_c=86.0),
            invoke_agent=True,
        )

    mock_agent.assert_awaited_once()
    assert result.agent_invoked is True
    assert result.agent_result is not None
    assert result.incident is not None
    assert result.incident.status == IncidentStatus.INVESTIGATING
    assert "Bearing degradation" in (result.incident.agent_summary or "")
    actions = [a["action"] for a in store.list_agent_actions()]
    assert "investigation_started" in actions
    assert "investigation_finished" in actions
