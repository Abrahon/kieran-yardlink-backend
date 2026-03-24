"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from invitations.views import accept_invite_page


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/',include('profiles.urls')),
    path('api/', include('chat.urls')),
    path('api/', include('message.urls')),
    path('api/',include('subscriptions.urls')),
    path('api/',include('landscapers.urls')),
    path('api/',include('services.urls')),
    path("api/", include("weather.urls")),
    path("api/", include("property.urls")),
    path("api/", include("invitations.urls")),
    path("accept-invite/<uuid:token>/", accept_invite_page, name="accept-invite-page"),
    path("api/", include("connections.urls")),
    path("api/", include("jobs.urls")),
    path("api/qr/", include("qr.urls")),
    path("api/", include("reviews.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("overview.urls")),
    path("api/", include("reports.urls")),
    path("api/", include("bookings.urls")),
    path("api/", include("notifications.urls")),
    path("api/", include("invoice.urls")),
    # path("api/", include("quickbooks.urls")),
]

