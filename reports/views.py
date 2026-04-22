from django.shortcuts import render
# Create your views here.
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from accounts.models import User
from subscriptions.enums import SubscriptionStatus
from .models import SiteVisit
from jobs.models import Job
from django.db.models import Q
from django.shortcuts import get_object_or_404
from accounts.models import User
from .serializers import AdminInternalNoteSerializer
from datetime import timedelta, datetime, time
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Count, Sum, FloatField, Value
from django.db.models.functions import Coalesce, TruncDate

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import status
from subscriptions.models import Subscription
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from accounts.models import User
from reports.models import AdminInternalNote
# from 
from payments.enums import PaymentStatus
from jobs.models import Job





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



# new
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

        return Response({"status": "success"}, status=status.HTTP_201_CREATED)




class AdminDashboardReportsView(APIView):
    permission_classes = [IsAdminUser]

    def get_percentage(self, count, total):
        if total <= 0:
            return 0.0
        return round((count / total) * 100, 2)

    def get_date_range(self, request):
        range_type = (request.query_params.get("range") or "").strip().lower()
        now = timezone.now()

        start_dt = None
        end_dt = now

        if range_type == "weekly":
            start_dt = now - timedelta(days=7)

        elif range_type == "monthly":
            start_dt = now - timedelta(days=30)

        elif range_type == "custom":
            start_date_str = request.query_params.get("start_date")
            end_date_str = request.query_params.get("end_date")

            start_date = parse_date(start_date_str) if start_date_str else None
            end_date = parse_date(end_date_str) if end_date_str else None

            if not start_date or not end_date:
                return None, None, Response(
                    {
                        "status": "error",
                        "message": "For custom range, start_date and end_date are required in YYYY-MM-DD format."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if start_date > end_date:
                return None, None, Response(
                    {
                        "status": "error",
                        "message": "start_date cannot be greater than end_date."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
            end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

        return start_dt, end_dt, None

    def apply_date_filter(self, queryset, field_name, start_dt, end_dt):
        if start_dt and end_dt:
            return queryset.filter(**{f"{field_name}__range": (start_dt, end_dt)})
        return queryset

    def should_export_csv(self, request):
        return (request.query_params.get("export") or "").strip().lower() == "csv"

    def export_csv_response(self, filename, headers, rows):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

        return response

    def get(self, request):
        start_dt, end_dt, error = self.get_date_range(request)
        if error:
            return error

        # -----------------------------------------
        # Shared filtered querysets
        # -----------------------------------------
        visits_qs = self.apply_date_filter(
            SiteVisit.objects.all(),
            "created_at",
            start_dt,
            end_dt
        )

        users_qs = self.apply_date_filter(
            User.objects.exclude(role="admin"),
            "date_joined",
            start_dt,
            end_dt
        )

        subscriptions_qs = self.apply_date_filter(
            Subscription.objects.all(),
            "created_at",
            start_dt,
            end_dt
        )

        revenue_qs = self.apply_date_filter(
            Job.objects.filter(payment_status=PaymentStatus.PAID),
            "created_at",
            start_dt,
            end_dt
        )

        # -----------------------------------------
        # 1) Acquisition Funnel
        # -----------------------------------------
        total_visitors = visits_qs.count()
        total_signups = users_qs.count()

        trial_signup_users = subscriptions_qs.filter(
            is_trial=True
        ).values_list("user_id", flat=True).distinct()
        trial_signups = len(set(trial_signup_users))

        paid_after_trial_users = subscriptions_qs.filter(
            user_id__in=trial_signup_users,
            is_trial=False,
            status__in=[
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.EXPIRED,
                SubscriptionStatus.CANCELLED
            ]
        ).values_list("user_id", flat=True).distinct()
        trial_to_paid = len(set(paid_after_trial_users))

        active_subscribers = subscriptions_qs.filter(
            status=SubscriptionStatus.ACTIVE,
            is_active=True
        ).values("user_id").distinct().count()

        # -----------------------------------------
        # 2) Conversion Metrics
        # -----------------------------------------
        quote_requested_count = 0
        quote_accepted_count = 0
        quote_conversion = self.get_percentage(quote_accepted_count, quote_requested_count)

        trial_signup_count = trial_signups
        visitor_to_trial_signup = self.get_percentage(trial_signup_count, total_visitors)

        paid_after_trial_count = len(set(paid_after_trial_users))
        trial_to_paid_conversion = self.get_percentage(paid_after_trial_count, trial_signup_count)

        all_subscriber_user_ids = subscriptions_qs.values_list("user_id", flat=True).distinct()
        total_subscribers_ever = len(set(all_subscriber_user_ids))

        active_subscriber_count = subscriptions_qs.filter(
            status=SubscriptionStatus.ACTIVE,
            is_active=True
        ).values("user_id").distinct().count()

        subscription_retention = self.get_percentage(active_subscriber_count, total_subscribers_ever)

        # -----------------------------------------
        # 3) User Concentration by Region
        # -----------------------------------------
        region_data = (
            users_qs
            .values("address")
            .annotate(user_count=Count("id"))
            .order_by("-user_count")[:10]
        )

        region_labels = []
        region_values = []

        for item in region_data:
            region_labels.append(item["address"] or "Unknown")
            region_values.append(item["user_count"])

        # -----------------------------------------
        # 4) User Growth (Line Chart)
        # -----------------------------------------
        growth_qs = (
            users_qs
            .annotate(day=TruncDate("date_joined"))
            .values("day")
            .annotate(total_users=Count("id"))
            .order_by("day")
        )

        growth_labels = []
        growth_values = []

        for row in growth_qs:
            growth_labels.append(row["day"].strftime("%Y-%m-%d"))
            growth_values.append(row["total_users"])

        # -----------------------------------------
        # 5) Revenue (Bar Chart)
        # -----------------------------------------
        revenue_grouped_qs = (
            revenue_qs
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Coalesce(Sum("service__price", output_field=FloatField()), Value(0.0)))
            .order_by("day")
        )

        revenue_labels = []
        revenue_values = []

        for row in revenue_grouped_qs:
            revenue_labels.append(row["day"].strftime("%Y-%m-%d"))
            revenue_values.append(round(float(row["total"]), 2))

        total_revenue = sum(revenue_values)

        response_data = {
            "status": "success",
            "filter": {
                "range": request.query_params.get("range", "all"),
                "start_date": request.query_params.get("start_date"),
                "end_date": request.query_params.get("end_date"),
            },
            "acquisition_funnel": {
                "total_visitors": {
                    "count": total_visitors,
                    "percentage": self.get_percentage(total_visitors, total_visitors)
                },
                "total_signups": {
                    "count": total_signups,
                    "percentage": self.get_percentage(total_signups, total_visitors)
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
            },
            "conversion_metrics": {
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
            },
            "user_concentration_by_region": {
                "title": "User Concentration by Region",
                "type": "bar",
                "labels": region_labels,
                "data": region_values
            },
            "user_growth": {
                "title": "User Growth",
                "type": "line",
                "labels": growth_labels,
                "data": growth_values,
                "total_users": users_qs.count()
            },
            "revenue": {
                "title": "Revenue",
                "type": "bar",
                "labels": revenue_labels,
                "data": revenue_values,
                "summary": {
                    "total_revenue": round(total_revenue, 2)
                }
            }
        }

        if self.should_export_csv(request):
            rows = [
                ["section", "metric", "value"],
                ["acquisition_funnel", "total_visitors", total_visitors],
                ["acquisition_funnel", "total_signups", total_signups],
                ["acquisition_funnel", "trial_signups", trial_signups],
                ["acquisition_funnel", "trial_to_paid", trial_to_paid],
                ["acquisition_funnel", "active_subscribers", active_subscribers],
                ["conversion_metrics", "quote_conversion", quote_conversion],
                ["conversion_metrics", "visitor_to_trial_signup", visitor_to_trial_signup],
                ["conversion_metrics", "trial_to_paid_conversion", trial_to_paid_conversion],
                ["conversion_metrics", "subscription_retention", subscription_retention],
                ["revenue", "total_revenue", round(total_revenue, 2)],
            ]

            for label, value in zip(growth_labels, growth_values):
                rows.append(["user_growth", label, value])

            for label, value in zip(region_labels, region_values):
                rows.append(["user_concentration_by_region", label, value])

            for label, value in zip(revenue_labels, revenue_values):
                rows.append(["revenue_chart", label, value])

            return self.export_csv_response(
                "admin_dashboard_analytics.csv",
                ["section", "metric", "value"],
                rows[1:]
            )

        return Response(response_data, status=status.HTTP_200_OK)




class AdminInternalNoteView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id=None):
        # single user note
        if user_id is not None:
            admin_note = (
                AdminInternalNote.objects
                .select_related("user", "created_by")
                .filter(user_id=user_id, is_active=True)
                .order_by("-created_at")
                .first()
            )

            if not admin_note:
                return Response(
                    {
                        "status": "error",
                        "message": "No active internal note found for this user."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = AdminInternalNoteSerializer(admin_note)
            return Response(
                {
                    "status": "success",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        # list all notes
        queryset = (
            AdminInternalNote.objects
            .select_related("user", "created_by")
            .order_by("-created_at")
        )

        search = request.query_params.get("search", "").strip()
        has_notes = request.query_params.get("has_notes")

        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__email__icontains=search)
            )

        if has_notes == "true":
            queryset = queryset.exclude(note__isnull=True).exclude(note__exact="")
        elif has_notes == "false":
            queryset = queryset.filter(
                Q(note__isnull=True) | Q(note__exact="")
            )

        serializer = AdminInternalNoteSerializer(queryset, many=True)

        return Response(
            {
                "status": "success",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, user_id):
        note = request.data.get("note")

        if note is None:
            return Response(
                {"status": "error", "message": "note is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, id=user_id)

        admin_note, created = AdminInternalNote.objects.update_or_create(
            user=user,
            is_active=True,
            defaults={
                "note": note,
                "created_by": request.user,
            },
        )

        serializer = AdminInternalNoteSerializer(admin_note)

        return Response(
            {
                "status": "success",
                "message": "Admin internal note saved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )