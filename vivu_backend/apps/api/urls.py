"""API URLs."""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Places
    path('places/', views.PlaceListView.as_view(), name='place-list'),
    path('places/search/', views.PlaceSearchView.as_view(), name='place-search'),
    path('places/<int:id>/', views.PlaceDetailView.as_view(), name='place-detail'),
    path('places/<int:id>/enriched/', views.PlaceEnrichedDetailView.as_view(), name='place-enriched-detail'),
    path('places/create/', views.PlaceCreateView.as_view(), name='place-create'),
    
    # Itineraries
    path('itineraries/', views.ItineraryListView.as_view(), name='itinerary-list'),
    path('itineraries/<int:id>/', views.ItineraryDetailView.as_view(), name='itinerary-detail'),
    
    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    
    # Location suggestions
    path('locations/suggestions/', views.LocationSuggestionsView.as_view(), name='location-suggestions'),
    path('locations/reverse-geocode/', views.ReverseGeocodeView.as_view(), name='reverse-geocode'),
    
    # AI Features (Legacy - for backward compatibility)
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('chat/itinerary/', views.ItineraryChatView.as_view(), name='chat-itinerary'),
    path('query/', views.QueryView.as_view(), name='query'),
    path('plan/', views.GeneratePlanView.as_view(), name='generate-plan'),
    
    # ML Recommendation APIs
    path('recommendations/content-based/', views.ContentBasedRecommendationView.as_view(), name='content-based-recommendation'),
    path('recommendations/cluster/', views.ClusterRecommendationView.as_view(), name='cluster-recommendation'),
    path('recommendations/predict-cost/', views.CostPredictionView.as_view(), name='predict-cost'),
    path('recommendations/hybrid/', views.HybridRecommendationView.as_view(), name='hybrid-recommendation'),
    
    # Travel Planning API với 7 Agents (RESTful)
    path('travel-plans/preview/', views.TravelPlanPreviewView.as_view(), name='travel-plan-preview'),
    path('travel-plans/', views.TravelPlanCreateView.as_view(), name='travel-plan-create'),
    
    # Workflow 4 Bước - API riêng cho từng step (chỉ dùng VietMap)
    path('travel-plans/step1/', views.Step1LocationSelectionView.as_view(), name='travel-plan-step1'),
    path('travel-plans/step2/', views.Step2TravelInfoView.as_view(), name='travel-plan-step2'),
    path('travel-plans/step3/', views.Step3BudgetSuggestionView.as_view(), name='travel-plan-step3'),
    path('travel-plans/step4/', views.Step4ConfirmAndPlanView.as_view(), name='travel-plan-step4'),
]

