# LangGraph Integration Notes

## Hiện trạng

- REST endpoint `POST /api/v1/travel-plans/` trong `vivu_backend/apps/api/travel_plan_views.py` đang gọi `OrchestratorAgent.execute()`.
- Workflow LangGraph đã tồn tại trong `vivu_backend/agents/langgraph_workflow.py`.
- Graph đã được compile tại:

```python
self.app = self.graph.compile(checkpointer=memory)
```

- Hàm wrapper hiện có sẵn:

```python
final_state = await self.app.ainvoke(state, config)
```

## Đề xuất thay thế `OrchestratorAgent.execute()`

Không sửa trực tiếp bây giờ, nhưng có thể thay adapter trong endpoint `travel-plans` theo hướng:

1. Import `LangGraphTravelWorkflow` thay cho `OrchestratorAgent`.
2. Dựng `initial_state` đúng shape của `TravelPlanningState`.
3. Gọi `await workflow.run(initial_state)` hoặc gọi trực tiếp `await workflow.app.ainvoke(...)`.
4. Giữ nguyên formatter response hiện tại để frontend không bị break.

## Pseudo-code đề xuất

```python
from agents.langgraph_workflow import LangGraphTravelWorkflow

workflow = LangGraphTravelWorkflow()

initial_state = {
    "origin": validated_data["origin"],
    "destination": validated_data["destination"],
    "start_date": validated_data["start_date"].strftime("%Y-%m-%d"),
    "days": validated_data["days"],
    "travelers": validated_data["travelers"],
    "travel_style": validated_data.get("travel_style", "standard"),
    "rooms": validated_data.get("rooms", 1),
    "interests": validated_data.get("interests", []),
}

if validated_data.get("budget"):
    initial_state["max_budget"] = validated_data["budget"]

if validated_data.get("selected_hotel"):
    initial_state["selected_hotel"] = validated_data["selected_hotel"]

async def run_plan_with_langgraph():
    return await workflow.run(
        initial_state,
        config={
            "configurable": {
                "thread_id": f"travel-plan-{request.user.pk or 'guest'}"
            }
        },
    )

result_state = await run_plan_with_langgraph()
```

## Vì sao nên gọi `workflow.run()` thay vì `workflow.app.ainvoke()` trực tiếp

- `workflow.run()` đã bọc sẵn:
  - khởi tạo `status='in_progress'`
  - `completed_steps=[]`
  - default `thread_id`
  - bắt lỗi và trả về `final_state` có `status='error'`

Nếu gọi thẳng `app.ainvoke()`, view sẽ phải tự lo các phần này.

## Mapping output cho frontend

Sau khi có `result_state`, response formatter hiện tại có thể giữ gần như nguyên:

```python
response_data = {
    "status": "success",
    "plan": {
        "transport": result_state.get("transport", {}),
        "flight": result_state.get("flight"),
        "hotels": result_state.get("hotels", []),
        "selected_hotel": result_state.get("selected_hotel"),
        "activities": result_state.get("activities", []),
        "restaurants": result_state.get("restaurants", []),
        "budget": result_state.get("budget", {}),
        "itinerary": result_state.get("itinerary", {}),
    },
    "costs": {
        "transport": result_state.get("transport_cost", 0),
        "accommodation": result_state.get("accommodation_cost", 0),
        "activities": result_state.get("activities_cost", 0),
        "dining": result_state.get("dining_cost", 0),
        "total": result_state.get("budget", {}).get("total_vnd", 0),
    },
}
```

## Rủi ro cần lưu ý trước khi bật thật

1. `LangGraphTravelWorkflow._accommodation_node()` hiện tính `check_out = start_date + days`, trong khi custom orchestrator có logic `nights = max(1, days - 1)`. Cần chuẩn hóa trước khi thay adapter.
2. `workflow.run()` hiện tạo `langsmith_config` nhưng chưa merge config đó vào lời gọi `ainvoke()`. Nếu cần tracing sâu hơn, chỗ này nên được nối lại khi tích hợp thật.
3. Cần test so sánh output giữa:
   - `OrchestratorAgent.execute(state)`
   - `LangGraphTravelWorkflow.run(state)`

Mục tiêu là frontend nhận cùng schema response trước khi chuyển hẳn.
