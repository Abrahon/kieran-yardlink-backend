# from django.urls import path
# from .views import ScanLandscaperQRCodeView

# urlpatterns = [
#      path("scan/<uuid:qr_id>/", ScanLandscaperQRCodeView.as_view()),
# ]
from django.urls import path
from .views import ScanLandscaperQRCodeView, GenerateQRCodeAPIView

urlpatterns = [
    path("generate/", GenerateQRCodeAPIView.as_view(), name="generate_qr"),
    path("scan/<uuid:qr_id>/", ScanLandscaperQRCodeView.as_view(), name="scan_qr"),
]
