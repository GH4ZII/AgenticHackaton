"""Phase 3 verification: agent independently chooses several tools."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.runtime import reset_store
from maintenance_agent.agent import root_agent

PROMPT = "Investigate PUMP-04."

ACTION_TOOLS = {
    "create_work_order",
    "notify_technician",
    "update_machine_status",
}


def _load_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)


async def main() -> int:
    _load_env()
    reset_store()

    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().upper() in {
        "1",
        "TRUE",
        "YES",
    }
    if use_vertex:
        required = [
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION",
        ]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            print(f"Missing env vars for Vertex: {', '.join(missing)}")
            print("Copy backend/.env.example to backend/.env and fill PROJECT_ID.")
            return 1
        if os.getenv("GOOGLE_CLOUD_PROJECT", "").startswith("<"):
            print("Set GOOGLE_CLOUD_PROJECT in backend/.env to a real GCP project ID.")
            return 1
    elif not os.getenv("GOOGLE_API_KEY"):
        print(
            "Set GOOGLE_GENAI_USE_VERTEXAI=TRUE with project/location, "
            "or provide GOOGLE_API_KEY for Gemini API."
        )
        return 1

    runner = InMemoryRunner(agent=root_agent, app_name="maintenance_agent")
    session = await runner.session_service.create_session(
        app_name="maintenance_agent",
        user_id="phase3",
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=PROMPT)],
    )

    tool_calls: list[str] = []
    final_text_parts: list[str] = []

    print(f"Prompt: {PROMPT}")
    print("---")

    async for event in runner.run_async(
        user_id="phase3",
        session_id=session.id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "function_call", None):
                    name = part.function_call.name
                    tool_calls.append(name)
                    print(f"[tool call] {name}({dict(part.function_call.args or {})})")
                elif getattr(part, "function_response", None):
                    print(f"[tool result] {part.function_response.name}")
                elif getattr(part, "text", None):
                    final_text_parts.append(part.text)

    final_text = "\n".join(final_text_parts).strip()
    unique_tools = set(tool_calls)

    print("---")
    print(final_text or "(no final text)")
    print("---")
    print(f"Tools called ({len(unique_tools)} unique): {sorted(unique_tools) or '(none)'}")

    if len(unique_tools) < 4:
        print("FAIL: expected at least 4 distinct tool calls.")
        return 2

    if not unique_tools.intersection(ACTION_TOOLS):
        print(
            "FAIL: expected at least one action tool "
            f"({', '.join(sorted(ACTION_TOOLS))})."
        )
        return 3

    if not final_text:
        print("FAIL: agent produced no maintenance decision text.")
        return 4

    print("PASS: agent independently used several tools and returned a decision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
