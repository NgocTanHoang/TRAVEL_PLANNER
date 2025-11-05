from django.urls import path
from .views import (SignupView, ProfileView, CustomPasswordChangeView, 
                    SearchHistoryView, UserItinerariesView, PlaceSearchView)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('search-history/', SearchHistoryView.as_view(), name='search_history'),
    path('itineraries/', UserItinerariesView.as_view(), name='itineraries'),
]

# Place search - separate namespace
place_search_patterns = [
    path('search/', PlaceSearchView.as_view(), name='place_search'),
]


