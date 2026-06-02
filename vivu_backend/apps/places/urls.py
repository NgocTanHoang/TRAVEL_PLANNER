from django.urls import path

from . import contribution_views

app_name = 'places'

urlpatterns = [
    # Unified contribution flow
    path('submit/', contribution_views.submit_place, name='submit_place'),
    path('submit/success/<int:pk>/', contribution_views.submit_success, name='pending_place_success'),
    path('my-submissions/', contribution_views.my_pending_places, name='my_pending_places'),
    
    # Admin URLs
    path('admin/pending-places/', contribution_views.pending_place_list, name='admin_pending_places'),
    path('admin/pending-places/<int:pk>/', contribution_views.review_pending_place, name='review_pending_place'),
]
