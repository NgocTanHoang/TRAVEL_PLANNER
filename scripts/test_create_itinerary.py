
import asyncio
from vivu_backend.agents.langgraph_workflow import run_travel_workflow

async def main():
    # Parameters for the travel plan
    origin = "Thành phố Hồ Chí Minh"
    destination = "Đà Nẵng"
    start_date = "2025-11-27"
    days = 3
    travelers = 2
    travel_style = "Văn hóa, Lịch sử"

    print(f"Creating a travel plan from {origin} to {destination} for {travelers} people for {days} days.")
    print(f"Travel style: {travel_style}")
    print("-" * 30)

    # Run the workflow
    final_state = await run_travel_workflow(
        origin=origin,
        destination=destination,
        start_date=start_date,
        days=days,
        travelers=travelers,
        travel_style=travel_style
    )

    # Print the final state
    print("-" * 30)
    print("Final Itinerary:")
    print(final_state)

if __name__ == "__main__":
    asyncio.run(main())
