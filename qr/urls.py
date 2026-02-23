# from django.urls import path
# from .views import ScanLandscaperQRCodeView

# urlpatterns = [
#      path("scan/<uuid:qr_id>/", ScanLandscaperQRCodeView.as_view()),
# ]
# from django.urls import path
# from .views import ScanLandscaperQRCodeView, GenerateQRCodeAPIView

# urlpatterns = [
#     path("generate/", GenerateQRCodeAPIView.as_view(), name="generate_qr"),
#     path("scan/<uuid:qr_id>/", ScanLandscaperQRCodeView.as_view(), name="scan_qr"),
# ]


# qr/urls.py
from django.urls import path
from .views import GenerateQRCodeAPIView, ScanLandscaperQRCodeView, GenerateInviteLinkAPIView, ScanInviteLinkAPIView

urlpatterns = [
    path("generate/", GenerateQRCodeAPIView.as_view(), name="generate_qr"),
    path("scan/<uuid:qr_id>/", ScanLandscaperQRCodeView.as_view(), name="scan_qr"),
    path("invite/generate/", GenerateInviteLinkAPIView.as_view(), name="generate_invite"),
    path("invite/<uuid:qr_id>/", ScanInviteLinkAPIView.as_view(), name="scan_invite"),
]
