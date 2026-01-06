from django.urls import path
from .views import ScanLandscaperQRCodeView

urlpatterns = [
     path("scan/<uuid:qr_id>/", ScanLandscaperQRCodeView.as_view()),
]
