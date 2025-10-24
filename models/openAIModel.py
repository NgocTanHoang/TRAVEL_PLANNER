"""
Mock OpenAI Model Client for Travel Planner Agents
This provides a simple interface for agents to use without requiring actual OpenAI API
"""

class MockModelClient:
    """Mock OpenAI model client for development and testing"""
    
    def __init__(self):
        self.model_name = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.max_tokens = 1000
        self.model_info = {
            "name": "gpt-3.5-turbo",
            "version": "mock-1.0",
            "capabilities": ["text-generation", "analysis", "planning"],
            "function_calling": True
        }
        self.function_calling = True
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate a mock response based on the prompt"""
        
        # Simple keyword-based responses for different types of requests
        prompt_lower = prompt.lower()
        
        if "plan" in prompt_lower or "itinerary" in prompt_lower:
            return self._generate_travel_plan_response(prompt, context)
        elif "research" in prompt_lower or "information" in prompt_lower:
            return self._generate_research_response(prompt, context)
        elif "recommend" in prompt_lower or "suggest" in prompt_lower:
            return self._generate_recommendation_response(prompt, context)
        elif "analyze" in prompt_lower or "sentiment" in prompt_lower:
            return self._generate_analysis_response(prompt, context)
        else:
            return self._generate_generic_response(prompt, context)
    
    def _generate_travel_plan_response(self, prompt: str, context: str) -> str:
        """Generate travel planning response"""
        return f"""
Travel Plan Generated:

Based on your request: "{prompt}"

Day 1:
- Morning: Visit historical sites
- Afternoon: Local cuisine experience
- Evening: Cultural activities

Day 2:
- Morning: Nature exploration
- Afternoon: Shopping and local markets
- Evening: Traditional entertainment

Day 3:
- Morning: Relaxation and wellness
- Afternoon: Additional attractions
- Evening: Farewell dinner

Budget Estimate: $150-300 per day
Recommendations: Book accommodations in advance, try local specialties
"""
    
    def _generate_research_response(self, prompt: str, context: str) -> str:
        """Generate research response"""
        return f"""
Research Insights:

Topic: {prompt}

Key Findings:
- Local customs and traditions
- Best times to visit
- Transportation options
- Safety considerations
- Cultural etiquette
- Language tips
- Currency and payment methods

Additional Context: {context[:100]}...
"""
    
    def _generate_recommendation_response(self, prompt: str, context: str) -> str:
        """Generate recommendation response"""
        return f"""
Recommendations:

Based on: {prompt}

Top Recommendations:
1. High-rated restaurants with authentic local cuisine
2. Must-visit attractions with cultural significance
3. Hidden gems known to locals
4. Budget-friendly options
5. Luxury experiences for special occasions

Context: {context[:100]}...
"""
    
    def _generate_analysis_response(self, prompt: str, context: str) -> str:
        """Generate analysis response"""
        return f"""
Analysis Results:

Analysis Type: {prompt}

Sentiment Analysis:
- Positive: 75%
- Neutral: 20%
- Negative: 5%

Key Insights:
- Overall sentiment is very positive
- Users appreciate authentic experiences
- Price-to-value ratio is excellent
- Service quality is consistently high

Recommendations:
- Continue current approach
- Focus on maintaining quality
- Consider expanding popular features
"""
    
    def _generate_generic_response(self, prompt: str, context: str) -> str:
        """Generate generic response"""
        return f"""
Response to: {prompt}

I understand your request and have processed the information. Here's my analysis:

Context: {context[:200]}...

Based on the available data and your requirements, I recommend:

1. Consider all available options
2. Evaluate based on your preferences
3. Make informed decisions
4. Plan ahead for the best experience

This response was generated using the mock model client for development purposes.
"""

# Global instance for agents to use
model_client = MockModelClient()
