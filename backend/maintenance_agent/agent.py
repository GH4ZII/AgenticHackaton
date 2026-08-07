from google.adk.agents.llm_agent import Agent

from .instructions import MAINTENANCE_AGENT_INSTRUCTION
from .tools import (
    check_inventory,
    create_work_order,
    get_machine_context,
    get_maintenance_history,
    get_telemetry_history,
    notify_technician,
    search_machine_manual,
    update_machine_status,
)

MODEL = "gemini-3.5-flash"

root_agent = Agent(
    name="maintenance_agent",
    model=MODEL,
    description="Industrial maintenance investigation agent",
    instruction=MAINTENANCE_AGENT_INSTRUCTION,
    tools=[
        get_machine_context,
        get_telemetry_history,
        get_maintenance_history,
        search_machine_manual,
        check_inventory,
        create_work_order,
        update_machine_status,
        notify_technician,
    ],
)
