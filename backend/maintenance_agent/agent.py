from google.adk.agents.llm_agent import Agent

from .instructions import MAINTENANCE_AGENT_INSTRUCTION
from .tools import get_machine_context, get_telemetry_history

MODEL = "gemini-3.5-flash"

root_agent = Agent(
    name="maintenance_agent",
    model=MODEL,
    description="Industrial maintenance investigation agent",
    instruction=MAINTENANCE_AGENT_INSTRUCTION,
    tools=[get_machine_context, get_telemetry_history],
)
