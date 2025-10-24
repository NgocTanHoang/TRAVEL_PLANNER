from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

class LangGraphNotAvailableError(RuntimeError):
    pass


def _require_langgraph():
    try:
        from langgraph.graph import StateGraph, END  # type: ignore
        from typing_extensions import TypedDict  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise LangGraphNotAvailableError(
            "LangGraph is not installed. Install with: pip install langgraph langchain-core"
        ) from exc
    return StateGraph, END, TypedDict


def build_travel_workflow_graph() -> Any:
    """Create a comprehensive StateGraph wiring 10 agents/components as nodes.
    
    Workflow topology:
    api_collector -> web_scraper -> data_processor -> 
    (recommendation + sentiment_analyzer + similarity_engine + price_predictor) -> 
    planner -> researcher -> analytics_engine -> END
    """
    StateGraph, END, TypedDict = _require_langgraph()

    class TravelState(TypedDict, total=False):
        # Input parameters
        destination: str
        budget: int
        days: int
        travelers: int
        
        # Workflow state
        collected_data: Dict[str, Any]
        scraped_data: Dict[str, Any]
        processed_data: Dict[str, Any]
        recommendations: Dict[str, Any]
        sentiment_analysis: Dict[str, Any]
        similarity_results: Dict[str, Any]
        price_predictions: Dict[str, Any]
        travel_plan: Dict[str, Any]
        research_insights: Dict[str, Any]
        analytics_results: Dict[str, Any]
        
        # Execution tracking
        steps_completed: List[str]
        errors: List[str]

    graph = StateGraph(TravelState)

    def _mark_step(step_name: str):
        def fn(state: Dict[str, Any]) -> Dict[str, Any]:
            steps = list(state.get("steps_completed", []))
            steps.append(step_name)
            state["steps_completed"] = steps
            return state
        return fn

    def _api_collector_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """API Collector node - fetch external travel data with caching"""
        try:
            destination = state.get("destination", "Hanoi")
            
            # Import and use real API collector
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from data_collection.api_collector import APICollector
            
            api_collector = APICollector()
            
            # Collect places data
            places_data = api_collector.collect_places_data(destination)
            
            # Get weather data
            weather_data = api_collector.get_weather_data(destination)
            
            # Search for travel information
            travel_info = api_collector.search_travel_info(f"travel guide {destination}")
            
            collected_data = {
                "places": places_data,
                "weather": weather_data,
                "travel_info": travel_info,
                "cache_stats": api_collector.get_cache_stats()
            }
            
            state["collected_data"] = collected_data
            return _mark_step("api_collector")(state)
            
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"API Collector error: {str(e)}")
            state["errors"] = errors
            return state

    def _web_scraper_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Web Scraper node - scrape additional sources with caching"""
        try:
            destination = state.get("destination", "Hanoi")
            
            # Import and use real web scraper
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from data_collection.web_scraper import WebScraper
            
            web_scraper = WebScraper()
            
            # Scrape places information
            places_data = web_scraper.scrape_places(destination)
            
            # Scrape hotels
            hotels = web_scraper.scrape_hotels(destination)
            
            # Scrape restaurants
            restaurants = web_scraper.scrape_restaurants(destination)
            
            # Scrape events
            events = web_scraper.scrape_events(destination)
            
            scraped_data = {
                "places": places_data,
                "hotels": hotels,
                "restaurants": restaurants,
                "events": events,
                "cache_stats": web_scraper.get_cache_stats()
            }
            
            state["scraped_data"] = scraped_data
            return _mark_step("web_scraper")(state)
            
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Web Scraper error: {str(e)}")
            state["errors"] = errors
            return state

    def _data_processor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Data Processor node - clean and normalize data"""
        try:
            collected = state.get("collected_data", {})
            scraped = state.get("scraped_data", {})
            
            # Combine and process data
            processed_data = {
                "places": [],
                "reviews": scraped.get("reviews", []),
                "events": scraped.get("events", [])
            }
            
            # Process places data
            for category, items in collected.items():
                for item in items:
                    processed_data["places"].append({
                        "name": item["name"],
                        "category": category,
                        "price_level": item.get("price_level", item.get("price", 0) // 50),
                        "rating": item["rating"],
                        "city": item["city"]
                    })
            
            state["processed_data"] = processed_data
            return _mark_step("data_processor")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Data Processor error: {str(e)}")
            state["errors"] = errors
            return state

    def _recommendation_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Recommendation Engine node - generate recommendations"""
        try:
            processed_data = state.get("processed_data", {})
            places = processed_data.get("places", [])
            
            # Simple recommendation logic
            recommendations = {
                "top_hotels": [p for p in places if p["category"] == "hotels" and p["rating"] >= 4.0][:3],
                "top_restaurants": [p for p in places if p["category"] == "restaurants" and p["rating"] >= 4.0][:3],
                "top_attractions": [p for p in places if p["category"] == "attractions" and p["rating"] >= 4.0][:3]
            }
            
            state["recommendations"] = recommendations
            return _mark_step("recommendation")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Recommendation error: {str(e)}")
            state["errors"] = errors
            return state

    def _sentiment_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Sentiment Analyzer node - analyze reviews"""
        try:
            processed_data = state.get("processed_data", {})
            reviews = processed_data.get("reviews", [])
            
            # Simple sentiment analysis
            sentiment_results = {
                "overall_sentiment": "positive",
                "positive_reviews": len([r for r in reviews if r["rating"] >= 4.0]),
                "negative_reviews": len([r for r in reviews if r["rating"] < 4.0]),
                "average_sentiment_score": sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0
            }
            
            state["sentiment_analysis"] = sentiment_results
            return _mark_step("sentiment_analyzer")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Sentiment Analyzer error: {str(e)}")
            state["errors"] = errors
            return state

    def _similarity_engine_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Similarity Engine node - find similar places"""
        try:
            processed_data = state.get("processed_data", {})
            places = processed_data.get("places", [])
            
            # Simple similarity calculation
            similarity_results = {
                "similar_places": [],
                "clusters": {
                    "budget": [p for p in places if p["price_level"] <= 2],
                    "mid_range": [p for p in places if 2 < p["price_level"] <= 3],
                    "premium": [p for p in places if p["price_level"] > 3]
                }
            }
            
            state["similarity_results"] = similarity_results
            return _mark_step("similarity_engine")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Similarity Engine error: {str(e)}")
            state["errors"] = errors
            return state

    def _price_predictor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Price Predictor node - predict costs"""
        try:
            budget = state.get("budget", 2000)
            days = state.get("days", 5)
            travelers = state.get("travelers", 2)
            
            # Simple price prediction
            price_predictions = {
                "estimated_costs": {
                    "accommodation": budget * 0.4,
                    "food": budget * 0.3,
                    "activities": budget * 0.2,
                    "transportation": budget * 0.1
                },
                "daily_budget": budget / days,
                "per_person_budget": budget / travelers,
                "budget_utilization": 0.85  # 85% utilization
            }
            
            state["price_predictions"] = price_predictions
            return _mark_step("price_predictor")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Price Predictor error: {str(e)}")
            state["errors"] = errors
            return state

    def _planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Planner node - create travel itinerary"""
        try:
            recommendations = state.get("recommendations", {})
            price_predictions = state.get("price_predictions", {})
            days = state.get("days", 5)
            
            # Create itinerary
            itinerary = {}
            for day in range(1, days + 1):
                itinerary[f"Day {day}"] = {
                    "morning": recommendations.get("top_attractions", [])[0]["name"] if recommendations.get("top_attractions") else "City exploration",
                    "afternoon": recommendations.get("top_attractions", [])[1]["name"] if len(recommendations.get("top_attractions", [])) > 1 else "Local activities",
                    "evening": recommendations.get("top_restaurants", [])[0]["name"] if recommendations.get("top_restaurants") else "Local dining",
                    "accommodation": recommendations.get("top_hotels", [])[0]["name"] if recommendations.get("top_hotels") else "Local hotel"
                }
            
            travel_plan = {
                "itinerary": itinerary,
                "estimated_costs": price_predictions.get("estimated_costs", {}),
                "total_days": days,
                "destination": state.get("destination", "Hanoi")
            }
            
            state["travel_plan"] = travel_plan
            return _mark_step("planner")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Planner error: {str(e)}")
            state["errors"] = errors
            return state

    def _researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Researcher node - enrich with additional research"""
        try:
            destination = state.get("destination", "Hanoi")
            travel_plan = state.get("travel_plan", {})
            
            # Add research insights
            research_insights = {
                "weather_info": f"Best time to visit {destination} is during dry season",
                "cultural_tips": f"Respect local customs in {destination}",
                "transportation": f"Use local transport in {destination} for authentic experience",
                "safety_tips": f"General safety precautions for {destination}",
                "local_events": "Check local calendar for festivals and events"
            }
            
            state["research_insights"] = research_insights
            return _mark_step("researcher")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Researcher error: {str(e)}")
            state["errors"] = errors
            return state

    def _analytics_engine_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Analytics Engine node - generate final insights"""
        try:
            # Combine all data for final analysis
            analytics_results = {
                "workflow_summary": {
                    "steps_completed": state.get("steps_completed", []),
                    "total_places_analyzed": len(state.get("processed_data", {}).get("places", [])),
                    "recommendations_generated": len(state.get("recommendations", {})),
                    "errors_encountered": len(state.get("errors", []))
                },
                "insights": [
                    f"Generated travel plan for {state.get('days', 5)} days in {state.get('destination', 'Hanoi')}",
                    f"Budget allocation optimized for ${state.get('budget', 2000)}",
                    f"Found {len(state.get('recommendations', {}).get('top_hotels', []))} recommended hotels",
                    f"Sentiment analysis shows {state.get('sentiment_analysis', {}).get('overall_sentiment', 'positive')} overall sentiment"
                ],
                "final_recommendations": state.get("recommendations", {}),
                "travel_plan": state.get("travel_plan", {}),
                "research_insights": state.get("research_insights", {})
            }
            
            state["analytics_results"] = analytics_results
            return _mark_step("analytics_engine")(state)
        except Exception as e:
            errors = list(state.get("errors", []))
            errors.append(f"Analytics Engine error: {str(e)}")
            state["errors"] = errors
            return state

    # Add nodes to graph
    graph.add_node("api_collector", _api_collector_node)
    graph.add_node("web_scraper", _web_scraper_node)
    graph.add_node("data_processor", _data_processor_node)
    graph.add_node("recommendation", _recommendation_node)
    graph.add_node("sentiment_analyzer", _sentiment_analyzer_node)
    graph.add_node("similarity_engine", _similarity_engine_node)
    graph.add_node("price_predictor", _price_predictor_node)
    graph.add_node("planner", _planner_node)
    graph.add_node("researcher", _researcher_node)
    graph.add_node("analytics_engine", _analytics_engine_node)

    # Define workflow topology
    graph.set_entry_point("api_collector")
    
    # Sequential: api_collector -> web_scraper -> data_processor
    graph.add_edge("api_collector", "web_scraper")
    graph.add_edge("web_scraper", "data_processor")
    
    # Parallel ML processing from data_processor
    graph.add_edge("data_processor", "recommendation")
    graph.add_edge("data_processor", "sentiment_analyzer")
    graph.add_edge("data_processor", "similarity_engine")
    graph.add_edge("data_processor", "price_predictor")
    
    # Converge to planner
    graph.add_edge("recommendation", "planner")
    graph.add_edge("sentiment_analyzer", "planner")
    graph.add_edge("similarity_engine", "planner")
    graph.add_edge("price_predictor", "planner")
    
    # Final sequence: planner -> researcher -> analytics_engine -> END
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "analytics_engine")
    graph.add_edge("analytics_engine", END)

    return graph.compile()


def run_travel_workflow(destination: str, budget: int, days: int, travelers: int, interests: str = "") -> Dict[str, Any]:
    """Run the complete travel planning workflow"""
    try:
        # Simple mock workflow execution for testing
        print(f"Running workflow for {destination}, {days} days, {budget:,} VND budget, {travelers} travelers, interests: {interests}")
        
        # Simulate workflow steps
        result = {
            "destination": destination,
            "budget": budget,
            "budget_currency": "VND",
            "days": days,
            "travelers": travelers,
            "interests": interests,
            "workflow_summary": {
                "steps_completed": ["api_collector", "data_processor", "planner", "analytics_engine"],
                "total_places_analyzed": 150,
                "recommendations_generated": 25,
                "errors_encountered": 0
            },
            "analytics_results": {
                "total_cost_estimate": budget * 0.8,  # 80% of budget
                "cost_currency": "VND",
                "recommended_places": 25,
                "average_rating": 4.3,
                "success_rate": 95,
                "budget_breakdown": {
                    "accommodation": budget * 0.4,  # 40% for hotels
                    "food": budget * 0.3,          # 30% for food
                    "transportation": budget * 0.15, # 15% for transport
                    "activities": budget * 0.15     # 15% for activities
                }
            },
            "workflow_result": "SUCCESS - Mock workflow completed"
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e), "workflow_result": "Workflow execution failed"}
