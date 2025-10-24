import os
# from dotenv import load_dotenv
# load_dotenv()  # Disabled due to encoding issues

class APIKeys:
    def __init__(self):
        # Google Cloud APIs - Direct assignment
    # Avoid hardcoding API keys in source. Read from environment variables instead.
    self.google_places = os.getenv('GOOGLE_PLACES_API_KEY')
    self.google_maps = os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Weather API
        self.openweather = os.getenv('OPENWEATHER_API_KEY')
        
        # Travel APIs
        self.opentripmap = os.getenv('OPENTRIPMAP_API_KEY')
        self.tavily = os.getenv('TAVILY_API_KEY')
        
        # Free APIs
        self.rest_countries = os.getenv('REST_COUNTRIES_ENABLED', 'false').lower() == 'true'
    
    def test_all_apis(self):
        """Test tất cả APIs"""
        results = {}
        
        # Test Google Places
        if self.google_places:
            try:
                import googlemaps
                gmaps = googlemaps.Client(key=self.google_places)
                places = gmaps.places_nearby(
                    location="Hanoi, Vietnam",
                    radius=1000,
                    type="tourist_attraction"
                )
                results['Google Places'] = f"✅ {len(places['results'])} places found"
            except Exception as e:
                results['Google Places'] = f"❌ Error: {str(e)[:50]}"
        else:
            results['Google Places'] = "❌ No API key"
        
        # Test OpenWeather
        if self.openweather:
            try:
                import requests
                response = requests.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q=Hanoi,VN&appid={self.openweather}&units=metric"
                )
                if response.status_code == 200:
                    data = response.json()
                    results['OpenWeather'] = f"✅ {data['main']['temp']}°C in {data['name']}"
                else:
                    results['OpenWeather'] = f"❌ HTTP {response.status_code}"
            except Exception as e:
                results['OpenWeather'] = f"❌ Error: {str(e)[:50]}"
        else:
            results['OpenWeather'] = "❌ No API key"
        
        # Test OpenTripMap
        if self.opentripmap:
            try:
                import requests
                response = requests.get(
                    f"https://api.opentripmap.com/0.1/en/places/radius?radius=10000&lon=105.8542&lat=21.0285&apikey={self.opentripmap}"
                )
                if response.status_code == 200:
                    data = response.json()
                    results['OpenTripMap'] = f"✅ {len(data['features'])} places found"
                else:
                    results['OpenTripMap'] = f"❌ HTTP {response.status_code}"
            except Exception as e:
                results['OpenTripMap'] = f"❌ Error: {str(e)[:50]}"
        else:
            results['OpenTripMap'] = "❌ No API key"
        
        # Test Tavily
        if self.tavily:
            try:
                import requests
                response = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily,
                        "query": "Hanoi Vietnam tourism",
                        "search_depth": "basic"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    results['Tavily'] = f"✅ {len(data['results'])} results found"
                else:
                    results['Tavily'] = f"❌ HTTP {response.status_code}"
            except Exception as e:
                results['Tavily'] = f"❌ Error: {str(e)[:50]}"
        else:
            results['Tavily'] = "❌ No API key"
        
        # Test REST Countries
        if self.rest_countries:
            try:
                import requests
                response = requests.get("https://restcountries.com/v3.1/name/vietnam")
                if response.status_code == 200:
                    data = response.json()
                    results['REST Countries'] = f"✅ {data[0]['name']['common']} found"
                else:
                    results['REST Countries'] = f"❌ HTTP {response.status_code}"
            except Exception as e:
                results['REST Countries'] = f"❌ Error: {str(e)[:50]}"
        else:
            results['REST Countries'] = "❌ Disabled"
        
        return results

# Test APIs
if __name__ == "__main__":
    api_keys = APIKeys()
    print("🔑 Testing all APIs...")
    print("=" * 60)
    
    results = api_keys.test_all_apis()
    for api, status in results.items():
        print(f"{api}: {status}")
    
    print("=" * 60)
    working_apis = [api for api, status in results.items() if "✅" in status]
    print(f"✅ Working APIs: {len(working_apis)}")
