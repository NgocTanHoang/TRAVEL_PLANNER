"""
URL configuration for Vi Vu project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from .views import serve_logo
from apps.users.views import PlaceSearchView, PlaceDetailView

urlpatterns = [
    # Home page - TripAppia-inspired design
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Travel Plan Workflow - 4 Steps
    path('travel-plan/', TemplateView.as_view(template_name='travel_plan.html'), name='travel-plan'),
    
    # AI Chat Assistant
    path('ai-chat/', TemplateView.as_view(template_name='ai_chat.html'), name='ai-chat'),
    
    # Place search
    path('places/search/', PlaceSearchView.as_view(), name='place_search'),
    path('places/<int:id>/', PlaceDetailView.as_view(), name='place_detail'),
    
    # Logo - Direct serve
    path('logo.png', serve_logo, name='logo'),
    
    # Technology Pages
    path('tech-django', TemplateView.as_view(template_name='tech-django.html'), name='tech-django'),
    path('tech-langchain', TemplateView.as_view(template_name='tech-langchain.html'), name='tech-langchain'),
    path('tech-gpt4', TemplateView.as_view(template_name='tech-gpt4.html'), name='tech-gpt4'),
    path('tech-chromadb', TemplateView.as_view(template_name='tech-chromadb.html'), name='tech-chromadb'),
    path('tech-multi-agent', TemplateView.as_view(template_name='tech-multi-agent.html'), name='tech-multi-agent'),
    
    # Authentication (login/logout) - templates/registration/
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Admin
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.users.urls')),
    
    # API v1
    path('api/v1/', include('apps.api.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve static and media files in development
if settings.DEBUG:
    # Serve static files from STATICFILES_DIRS
    import os
    for directory in settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=directory)
    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

