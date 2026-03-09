from django.shortcuts import render
# Create your views here.
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from subscriptions.models import Subscription
from subscriptions.enums import SubscriptionStatus
from .models import SiteVisit


from .models import SiteVisit


class TrackVisitAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        ua = request.META.get("HTTP_USER_AGENT", "")
        path = request.data.get("path")

        SiteVisit.objects.create(
            ip_address=ip,
            user_agent=ua,
            path=path
        )

        return Response({"status": "success"})






class AdminAcquisitionFunnelView(APIView):
    permission_classes = [IsAdminUser]

    def get_percentage(self, count, total):
        if total <= 0:
            return 0.0
        return round((count / total) * 100, 2)

    def get(self, request):
        total_visitors = SiteVisit.objects.count()

        # total signups = all users except admins if you want marketplace users only
        total_signups = User.objects.exclude(role="admin").count()

        # users who started with trial subscriptions
        trial_signup_users = Subscription.objects.filter(
            is_trial=True
        ).values_list("user_id", flat=True).distinct()

        trial_signups = len(set(trial_signup_users))

        # users who had trial before and now are on paid/non-trial subscription
        paid_after_trial_users = Subscription.objects.filter(
            user_id__in=trial_signup_users,
            is_trial=False,
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED]
        ).values_list("user_id", flat=True).distinct()

        trial_to_paid = len(set(paid_after_trial_users))

        active_subscribers = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            is_active=True
        ).values("user_id").distinct().count()

        return Response({
            "status": "success",
            "funnel": {
                "total_visitors": {
                    "count": total_visitors,
                    "percentage": self.get_percentage(total_visitors, total_visitors)
                },
                "trial_signups": {
                    "count": trial_signups,
                    "percentage": self.get_percentage(trial_signups, total_visitors)
                },
                "trial_to_paid": {
                    "count": trial_to_paid,
                    "percentage": self.get_percentage(trial_to_paid, total_visitors)
                },
                "active_subscribers": {
                    "count": active_subscribers,
                    "percentage": self.get_percentage(active_subscribers, total_visitors)
                }
            }
        }, status=status.HTTP_200_OK)

# qute conversion
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAdminUser
# from rest_framework.response import Response
# from rest_framework import status

# from accounts.models import User
# from subscriptions.models import Subscription
# from subscriptions.enums import SubscriptionStatus
# from overview.models import SiteVisit   # change if your app/model path differs

# -----------------------------------------
# OPTIONAL: replace this with your real quote model
# -----------------------------------------
# Example assumption:
# from quotes.models import QuoteRequest
#
# class QuoteRequest(models.Model):
#     status = models.CharField(max_length=30)  # requested / accepted / rejected
#     created_at = models.DateTimeField(auto_now_add=True)



class AdminConversionMetricsView(APIView):
    permission_classes = [IsAdminUser]

    def get_percentage(self, count, total):
        if total <= 0:
            return 0.0
        return round((count / total) * 100, 2)

    def get(self, request):
        # -----------------------------------------
        # 1) Quote Requested -> Accepted
        # -----------------------------------------
        quote_requested_count = 0
        quote_accepted_count = 0
        quote_conversion = self.get_percentage(quote_accepted_count, quote_requested_count)

        # -----------------------------------------
        # 2) Visitor -> Trial Signup
        # -----------------------------------------
        total_visitors = SiteVisit.objects.count()

        trial_signup_user_ids = Subscription.objects.filter(
            is_trial=True
        ).values_list("user_id", flat=True).distinct()

        trial_signup_count = len(set(trial_signup_user_ids))
        visitor_to_trial_signup = self.get_percentage(trial_signup_count, total_visitors)

        # -----------------------------------------
        # 3) Trial -> Paid Conversion
        # -----------------------------------------
        paid_after_trial_user_ids = Subscription.objects.filter(
            user_id__in=trial_signup_user_ids,
            is_trial=False,
            status__in=[
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.EXPIRED,
                SubscriptionStatus.CANCELLED,
            ]
        ).values_list("user_id", flat=True).distinct()

        paid_after_trial_count = len(set(paid_after_trial_user_ids))
        trial_to_paid_conversion = self.get_percentage(paid_after_trial_count, trial_signup_count)

        # -----------------------------------------
        # 4) Subscription Retention
        # -----------------------------------------
        all_subscriber_user_ids = Subscription.objects.values_list("user_id", flat=True).distinct()
        total_subscribers_ever = len(set(all_subscriber_user_ids))

        active_subscriber_count = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            is_active=True
        ).values("user_id").distinct().count()

        subscription_retention = self.get_percentage(active_subscriber_count, total_subscribers_ever)

        return Response({
            "status": "success",
            "metrics": {
                "quote_conversion": {
                    "title": "Quote Conversion",
                    "value": quote_conversion,
                    "unit": "%",
                    "label": "Quote Requested → Accepted",
                    "requested_count": quote_requested_count,
                    "accepted_count": quote_accepted_count
                },
                "visitor_to_trial_signup": {
                    "title": "Visitor → Trial Signup",
                    "value": visitor_to_trial_signup,
                    "unit": "%",
                    "label": "Visitor → Trial Signup",
                    "visitor_count": total_visitors,
                    "trial_signup_count": trial_signup_count
                },
                "trial_to_paid_conversion": {
                    "title": "Trial → Paid Conversion",
                    "value": trial_to_paid_conversion,
                    "unit": "%",
                    "label": "Trial → Paid Conversion",
                    "trial_signup_count": trial_signup_count,
                    "paid_after_trial_count": paid_after_trial_count
                },
                "subscription_retention": {
                    "title": "Subscription Retention",
                    "value": subscription_retention,
                    "unit": "%",
                    "label": "Subscription Retention",
                    "active_subscribers": active_subscriber_count,
                    "total_subscribers_ever": total_subscribers_ever
                }
            }
        }, status=status.HTTP_200_OK)

# user by region
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User

class UserConcentrationByRegionView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        region_data = (
            User.objects
            .exclude(role="admin")
            .values("address")
            .annotate(user_count=Count("id"))
            .order_by("-user_count")[:10]
        )

        labels = []
        data = []

        for item in region_data:
            labels.append(item["address"] or "Unknown")
            data.append(item["user_count"])

        return Response({
            "status": "success",
            "chart": {
                "title": "User Concentration by Region",
                "type": "bar",
                "labels": labels,
                "data": data
            }
        }, status=status.HTTP_200_OK)