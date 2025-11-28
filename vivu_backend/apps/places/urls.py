from django.urls import path
from . import views_pending

app_name = 'places'

urlpatterns = [
    # Pending places
    path('submit/', views_pending.submit_place, name='submit_place'),
    path('submit/success/<int:pk>/', views_pending.submit_success, name='pending_place_success'),
    path('my-submissions/', views_pending.my_pending_places, name='my_pending_places'),
    
    # Admin URLs
    path('admin/pending-places/', views_pending.pending_place_list, name='admin_pending_places'),
    path('admin/pending-places/<int:pk>/', views_pending.review_pending_place, name='review_pending_place'),
]
