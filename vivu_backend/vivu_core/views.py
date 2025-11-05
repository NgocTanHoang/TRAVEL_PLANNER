"""
Vi Vu Core Views
"""
from django.http import FileResponse, Http404
from django.conf import settings
import os


def serve_logo(request):
    """Serve logo_crop-Photoroom.png directly from staticfiles"""
    # Ưu tiên sử dụng logo_crop-Photoroom.png (logo mới đã remove background)
    logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo_crop-Photoroom.png')
    fallback_logo_crop = os.path.join(settings.STATIC_ROOT, 'img', 'logo_crop.png')
    fallback_logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo.png')
    
    # Kiểm tra staticfiles trước
    if os.path.exists(logo_path):
        return FileResponse(open(logo_path, 'rb'), content_type='image/png')
    elif os.path.exists(fallback_logo_crop):
        return FileResponse(open(fallback_logo_crop, 'rb'), content_type='image/png')
    elif os.path.exists(fallback_logo_path):
        return FileResponse(open(fallback_logo_path, 'rb'), content_type='image/png')
    else:
        # Fallback to source static folder in case collectstatic hasn't run yet
        source_logo_photoroom = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_crop-Photoroom.png')
        source_logo_crop = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_crop.png')
        source_logo = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
        
        if os.path.exists(source_logo_photoroom):
            return FileResponse(open(source_logo_photoroom, 'rb'), content_type='image/png')
        elif os.path.exists(source_logo_crop):
            return FileResponse(open(source_logo_crop, 'rb'), content_type='image/png')
        elif os.path.exists(source_logo):
            return FileResponse(open(source_logo, 'rb'), content_type='image/png')
        raise Http404("Logo not found")

