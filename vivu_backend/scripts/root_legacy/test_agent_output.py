"""
Script chay thu nhanh he thong agent voi LLM that va ghi structured output ra file JSON.

Usage:
    py scripts/test_agent_output.py

Feature flag:
    USE_LANGGRAPH_WORKFLOW=true  -> dung LangGraphTravelWorkflow
    USE_LANGGRAPH_WORKFLOW=false -> dung OrchestratorAgent
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "vivu_backend"
OUTPUT_PATH = REPO_ROOT / "agent_output_test.json"
ENV_PATH = REPO_ROOT / ".env"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def build_test_state() -> Dict[str, Any]:
    """Tao input test co y nghia de chay full workflow."""
    return {
        "origin": "Ha Noi",
        "destination": "Quang Ninh",
        "start_date": "2026-06-15",
        "days": 2,
        "travelers": 2,
        "travel_style": "standard",
        "rooms": 1,
        "interests": ["bien", "am thuc", "tham quan"],
        "max_budget": 5000000,
    }


def setup_runtime() -> None:
    """Nap .env va bootstrap Django truoc khi goi agents."""
    load_dotenv(dotenv_path=ENV_PATH, override=False, encoding="utf-8-sig")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_backend.vivu_core.settings")

    import django  # noqa: E402

    django.setup()


async def run_agent_flow(state: Dict[str, Any]) -> Dict[str, Any]:
    """Chon engine theo feature flag va chay workflow that."""
    setup_runtime()
    use_langgraph_workflow = os.environ.get("USE_LANGGRAPH_WORKFLOW", "False").lower() == "true"

    if use_langgraph_workflow:
        from vivu_backend.agents.langgraph_workflow import LangGraphTravelWorkflow

        workflow = LangGraphTravelWorkflow()
        return await workflow.run(
            state,
            config={
                "configurable": {
                    "thread_id": "script-test-agent-output",
                }
            },
        )

    from vivu_backend.agents.travel_agents.orchestrator_agent import OrchestratorAgent

    orchestrator = OrchestratorAgent()
    return await orchestrator.execute(state)


async def main() -> None:
    """Chay workflow that va ghi itinerary_json ra file local."""
    final_state = await run_agent_flow(build_test_state())

    if final_state.get("status") == "error":
        raise RuntimeError(final_state.get("error", "Workflow tra ve trang thai loi"))

    itinerary_json = final_state.get("itinerary_json")
    if not itinerary_json:
        planning_error = final_state.get("planning_error")
        if planning_error:
            raise RuntimeError(f"Khong nhan duoc itinerary_json: {planning_error}")
        raise ValueError("Khong nhan duoc state['itinerary_json'] tu workflow.")

    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        json.dump(itinerary_json, output_file, ensure_ascii=False, indent=2)

    print(f"Da ghi ket qua vao: {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
