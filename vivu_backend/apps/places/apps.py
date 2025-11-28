"""Places app configuration."""
from django.apps import AppConfig


class PlacesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.places'
    verbose_name = 'Địa điểm'
    
    def ready(self):
        # Import models here to avoid circular imports
        from .models import PendingPlace, PendingPlaceImage
        return super().ready()

