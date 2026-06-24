from django.shortcuts import render

# Create your views here.
from datetime import timedelta, datetime
from calendar import monthrange
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from jobs.models import Job
from subscriptions.models import Subscription, SubscriptionStatus
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from accounts .models import User
from payments.enums import PaymentStatus




def percentage_change(current, previous):
    if previous == 0:
        if current == 0:
            return 0.0, "no_change"
        return 100.0, "increase"
    change = ((current - previous) / previous) * 100
    if change > 0:
        return round(change, 2), "increase"
    if change < 0:
        return round(change, 2), "decrease"
    return 0.0, "no_change"


def start_of_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_month(dt):
    last_day = monthrange(dt.year, dt.month)[1]
    return dt.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)


def add_months(dt, months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


class AdminTotalUsersAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()

        # -------------------------
        # Total users
        # -------------------------
        total_users = User.objects.count()

        # Compare total users now vs end of last month
        current_month_start = start_of_month(now)
        last_month_end = current_month_start - timedelta(microseconds=1)
        total_until_last_month = User.objects.filter(
            date_joined__lte=last_month_end
        ).count()

        total_change_pct, total_change_direction = percentage_change(
            total_users, total_until_last_month
        )

        # -------------------------
        # 6-month cumulative trend
        # -------------------------
        # Example: Aug, Sep, Oct, Nov, Dec, Jan
        trend = []
        for i in range(5, -1, -1):
            month_date = add_months(current_month_start, -i)
            month_end = end_of_month(month_date)
            cumulative_total = User.objects.filter(
                date_joined__lte=month_end
            ).count()

            trend.append({
                "label": month_date.strftime("%b"),
                "year": month_date.year,
                "month": month_date.month,
                "total_users": cumulative_total
            })

        # -------------------------
        # This week vs previous week
        # -------------------------
        weekday = now.weekday()  # Monday=0
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_count = User.objects.filter(
            date_joined__gte=this_week_start,
            date_joined__lt=next_week_start
        ).count()

        prev_week_count = User.objects.filter(
            date_joined__gte=prev_week_start,
            date_joined__lt=this_week_start
        ).count()

        this_week_pct, this_week_direction = percentage_change(
            this_week_count, prev_week_count
        )

        # -------------------------
        # This month vs last month
        # -------------------------
        this_month_start = current_month_start
        next_month_start = add_months(this_month_start, 1)
        last_month_start = add_months(this_month_start, -1)

        this_month_count = User.objects.filter(
            date_joined__gte=this_month_start,
            date_joined__lt=next_month_start
        ).count()

        last_month_count = User.objects.filter(
            date_joined__gte=last_month_start,
            date_joined__lt=this_month_start
        ).count()

        this_month_pct, this_month_direction = percentage_change(
            this_month_count, last_month_count
        )

        # -------------------------
        # Last month vs month before last
        # -------------------------
        month_before_last_start = add_months(last_month_start, -1)

        month_before_last_count = User.objects.filter(
            date_joined__gte=month_before_last_start,
            date_joined__lt=last_month_start
        ).count()

        last_month_pct, last_month_direction = percentage_change(
            last_month_count, month_before_last_count
        )

        # -------------------------
        # Last quarter vs previous quarter
        # -------------------------
        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_end = current_quarter_start
        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_count = User.objects.filter(
            date_joined__gte=last_quarter_start,
            date_joined__lt=last_quarter_end
        ).count()

        prev_quarter_count = User.objects.filter(
            date_joined__gte=prev_quarter_start,
            date_joined__lt=last_quarter_start
        ).count()

        last_quarter_pct, last_quarter_direction = percentage_change(
            last_quarter_count, prev_quarter_count
        )

        return Response({
            "status": "success",
            "metric": "total_users",
            "card": {
                "title": "Total Users",
                "value": total_users,
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month"
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": this_week_count,
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": this_month_count,
                    "change_percentage": this_month_pct,
                    "change_direction": this_month_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": last_month_count,
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": last_quarter_count,
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)

# total client
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from accounts.enums import RoleChoices


class AdminTotalClientsAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()

        total_clients = User.objects.filter(role=RoleChoices.CLIENT).count()

        current_month_start = start_of_month(now)
        last_month_end = current_month_start - timedelta(microseconds=1)

        total_until_last_month = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__lte=last_month_end
        ).count()

        total_change_pct, total_change_direction = percentage_change(
            total_clients, total_until_last_month
        )

        trend = []
        for i in range(5, -1, -1):
            month_date = add_months(current_month_start, -i)
            month_end = end_of_month(month_date)

            cumulative_total = User.objects.filter(
                role=RoleChoices.CLIENT,
                date_joined__lte=month_end
            ).count()

            trend.append({
                "label": month_date.strftime("%b"),
                "year": month_date.year,
                "month": month_date.month,
                "total_clients": cumulative_total
            })

        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_count = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__gte=this_week_start,
            date_joined__lt=next_week_start
        ).count()

        prev_week_count = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__gte=prev_week_start,
            date_joined__lt=this_week_start
        ).count()

        this_week_pct, this_week_direction = percentage_change(this_week_count, prev_week_count)

        this_month_start = current_month_start
        next_month_start = add_months(this_month_start, 1)
        last_month_start = add_months(this_month_start, -1)

        this_month_count = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__gte=this_month_start,
            date_joined__lt=next_month_start
        ).count()

        last_month_count = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__gte=last_month_start,
            date_joined__lt=this_month_start
        ).count()

        this_month_pct, this_month_direction = percentage_change(this_month_count, last_month_count)

        month_before_last_start = add_months(last_month_start, -1)

        month_before_last_count = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__gte=month_before_last_start,
            date_joined__lt=last_month_start
        ).count()

        last_month_pct, last_month_direction = percentage_change(last_month_count, month_before_last_count)

        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_end = current_quarter_start
        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_count = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__gte=last_quarter_start,
            date_joined__lt=last_quarter_end
        ).count()

        prev_quarter_count = User.objects.filter(
            role=RoleChoices.CLIENT,
            date_joined__gte=prev_quarter_start,
            date_joined__lt=last_quarter_start
        ).count()

        last_quarter_pct, last_quarter_direction = percentage_change(last_quarter_count, prev_quarter_count)

        return Response({
            "status": "success",
            "metric": "total_clients",
            "card": {
                "title": "Total Clients",
                "value": total_clients,
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month"
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": this_week_count,
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": this_month_count,
                    "change_percentage": this_month_pct,
                    "change_direction": this_month_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": last_month_count,
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": last_quarter_count,
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)


# total landscapers
class AdminTotalLandscapersAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()

        total_landscapers = User.objects.filter(role=RoleChoices.LANDSCAPER).count()

        current_month_start = start_of_month(now)
        last_month_end = current_month_start - timedelta(microseconds=1)

        total_until_last_month = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__lte=last_month_end
        ).count()

        total_change_pct, total_change_direction = percentage_change(
            total_landscapers, total_until_last_month
        )

        trend = []
        for i in range(5, -1, -1):
            month_date = add_months(current_month_start, -i)
            month_end = end_of_month(month_date)

            cumulative_total = User.objects.filter(
                role=RoleChoices.LANDSCAPER,
                date_joined__lte=month_end
            ).count()

            trend.append({
                "label": month_date.strftime("%b"),
                "year": month_date.year,
                "month": month_date.month,
                "total_landscapers": cumulative_total
            })

        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_count = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__gte=this_week_start,
            date_joined__lt=next_week_start
        ).count()

        prev_week_count = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__gte=prev_week_start,
            date_joined__lt=this_week_start
        ).count()

        this_week_pct, this_week_direction = percentage_change(this_week_count, prev_week_count)

        this_month_start = current_month_start
        next_month_start = add_months(this_month_start, 1)
        last_month_start = add_months(this_month_start, -1)

        this_month_count = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__gte=this_month_start,
            date_joined__lt=next_month_start
        ).count()

        last_month_count = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__gte=last_month_start,
            date_joined__lt=this_month_start
        ).count()

        this_month_pct, this_month_direction = percentage_change(this_month_count, last_month_count)

        month_before_last_start = add_months(last_month_start, -1)

        month_before_last_count = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__gte=month_before_last_start,
            date_joined__lt=last_month_start
        ).count()

        last_month_pct, last_month_direction = percentage_change(last_month_count, month_before_last_count)

        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_end = current_quarter_start
        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_count = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__gte=last_quarter_start,
            date_joined__lt=last_quarter_end
        ).count()

        prev_quarter_count = User.objects.filter(
            role=RoleChoices.LANDSCAPER,
            date_joined__gte=prev_quarter_start,
            date_joined__lt=last_quarter_start
        ).count()

        last_quarter_pct, last_quarter_direction = percentage_change(last_quarter_count, prev_quarter_count)

        return Response({
            "status": "success",
            "metric": "total_landscapers",
            "card": {
                "title": "Total Landscapers",
                "value": total_landscapers,
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month"
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": this_week_count,
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": this_month_count,
                    "change_percentage": this_month_pct,
                    "change_direction": this_month_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": last_month_count,
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": last_quarter_count,
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)

# basic subscription
from subscriptions.models import Subscription, SubscriptionStatus


class BaseSubscriptionPlanAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    plan_name = None
    metric_name = None
    card_title = None

    def get_plan_queryset(self):
        return Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            is_active=True,
            plan__name__iexact=self.plan_name
        )

    def get(self, request):
        now = timezone.now()
        qs = self.get_plan_queryset()

        total_count = qs.count()

        current_month_start = start_of_month(now)
        last_month_end = current_month_start - timedelta(microseconds=1)

        total_until_last_month = qs.filter(
            created_at__lte=last_month_end
        ).count()

        total_change_pct, total_change_direction = percentage_change(
            total_count, total_until_last_month
        )

        trend = []
        for i in range(5, -1, -1):
            month_date = add_months(current_month_start, -i)
            month_end = end_of_month(month_date)

            cumulative_total = qs.filter(
                created_at__lte=month_end
            ).count()

            trend.append({
                "label": month_date.strftime("%b"),
                "year": month_date.year,
                "month": month_date.month,
                "active_subscriptions": cumulative_total
            })

        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_count = qs.filter(
            created_at__gte=this_week_start,
            created_at__lt=next_week_start
        ).count()

        prev_week_count = qs.filter(
            created_at__gte=prev_week_start,
            created_at__lt=this_week_start
        ).count()

        this_week_pct, this_week_direction = percentage_change(this_week_count, prev_week_count)

        this_month_start = current_month_start
        next_month_start = add_months(this_month_start, 1)
        last_month_start = add_months(this_month_start, -1)

        this_month_count = qs.filter(
            created_at__gte=this_month_start,
            created_at__lt=next_month_start
        ).count()

        last_month_count = qs.filter(
            created_at__gte=last_month_start,
            created_at__lt=this_month_start
        ).count()

        this_month_pct, this_month_direction = percentage_change(this_month_count, last_month_count)

        month_before_last_start = add_months(last_month_start, -1)

        month_before_last_count = qs.filter(
            created_at__gte=month_before_last_start,
            created_at__lt=last_month_start
        ).count()

        last_month_pct, last_month_direction = percentage_change(last_month_count, month_before_last_count)

        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_end = current_quarter_start
        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_count = qs.filter(
            created_at__gte=last_quarter_start,
            created_at__lt=last_quarter_end
        ).count()

        prev_quarter_count = qs.filter(
            created_at__gte=prev_quarter_start,
            created_at__lt=last_quarter_start
        ).count()

        last_quarter_pct, last_quarter_direction = percentage_change(last_quarter_count, prev_quarter_count)

        return Response({
            "status": "success",
            "metric": self.metric_name,
            "card": {
                "title": self.card_title,
                "value": total_count,
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month"
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": this_week_count,
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": this_month_count,
                    "change_percentage": this_month_pct,
                    "change_direction": this_month_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": last_month_count,
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": last_quarter_count,
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)

# basic subscription
class AdminActiveBasicSubscriptionsAnalyticsView(BaseSubscriptionPlanAnalyticsView):
    plan_name = "Basic"
    metric_name = "active_basic_subscriptions"
    card_title = "Active Basic Subscriptions"


# pro subscription
class AdminActiveProSubscriptionsAnalyticsView(BaseSubscriptionPlanAnalyticsView):
    plan_name = "Pro"
    metric_name = "active_pro_subscriptions"
    card_title = "Active Pro Subscriptions"



# job completd 

class AdminJobsCompletedAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()

        qs = Job.objects.filter(status=Job.Status.COMPLETED)

        total_completed_jobs = qs.count()

        current_month_start = start_of_month(now)
        last_month_end = current_month_start - timedelta(microseconds=1)

        total_until_last_month = qs.filter(
            completed_at__isnull=False,
            completed_at__lte=last_month_end
        ).count()

        total_change_pct, total_change_direction = percentage_change(
            total_completed_jobs, total_until_last_month
        )

        trend = []
        for i in range(5, -1, -1):
            month_date = add_months(current_month_start, -i)
            month_end = end_of_month(month_date)

            cumulative_total = qs.filter(
                completed_at__isnull=False,
                completed_at__lte=month_end
            ).count()

            trend.append({
                "label": month_date.strftime("%b"),
                "year": month_date.year,
                "month": month_date.month,
                "jobs_completed": cumulative_total
            })

        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_count = qs.filter(
            completed_at__gte=this_week_start,
            completed_at__lt=next_week_start
        ).count()

        prev_week_count = qs.filter(
            completed_at__gte=prev_week_start,
            completed_at__lt=this_week_start
        ).count()

        this_week_pct, this_week_direction = percentage_change(this_week_count, prev_week_count)

        this_month_start = current_month_start
        next_month_start = add_months(this_month_start, 1)
        last_month_start = add_months(this_month_start, -1)

        this_month_count = qs.filter(
            completed_at__gte=this_month_start,
            completed_at__lt=next_month_start
        ).count()

        last_month_count = qs.filter(
            completed_at__gte=last_month_start,
            completed_at__lt=this_month_start
        ).count()

        this_month_pct, this_month_direction = percentage_change(this_month_count, last_month_count)

        month_before_last_start = add_months(last_month_start, -1)

        month_before_last_count = qs.filter(
            completed_at__gte=month_before_last_start,
            completed_at__lt=last_month_start
        ).count()

        last_month_pct, last_month_direction = percentage_change(last_month_count, month_before_last_count)

        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_end = current_quarter_start
        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_count = qs.filter(
            completed_at__gte=last_quarter_start,
            completed_at__lt=last_quarter_end
        ).count()

        prev_quarter_count = qs.filter(
            completed_at__gte=prev_quarter_start,
            completed_at__lt=last_quarter_start
        ).count()

        last_quarter_pct, last_quarter_direction = percentage_change(last_quarter_count, prev_quarter_count)

        return Response({
            "status": "success",
            "metric": "jobs_completed",
            "card": {
                "title": "Jobs Completed",
                "value": total_completed_jobs,
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month"
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": this_week_count,
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": this_month_count,
                    "change_percentage": this_month_pct,
                    "change_direction": this_month_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": last_month_count,
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": last_quarter_count,
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)





# admin churn rate

def percentage_change(current, previous):
    if previous == 0:
        if current == 0:
            return 0.0, "no_change"
        return 100.0, "increase"
    change = ((current - previous) / previous) * 100
    if change > 0:
        return round(change, 2), "increase"
    if change < 0:
        return round(abs(change), 2), "decrease"
    return 0.0, "no_change"


def start_of_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def add_months(dt, months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


class AdminChurnRateAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def _period_churn_data(self, start_date, end_date):
        # Active at the START of the period
        starting_active = Subscription.objects.filter(
            start_date__lt=start_date,
            end_date__gte=start_date,
            is_active=True
        ).exclude(
            status__in=[SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]
        ).count()

        # ✅ Use cancelled_at for cancellation period tracking
        cancelled_count = Subscription.objects.filter(
            status=SubscriptionStatus.CANCELLED,
            cancelled_at__isnull=False,
            cancelled_at__gte=start_date,
            cancelled_at__lt=end_date
        ).count()

        # For expired, if you do NOT yet have expired_at field,
        # use end_date as the closest period marker
        expired_count = Subscription.objects.filter(
            status=SubscriptionStatus.EXPIRED,
            end_date__gte=start_date,
            end_date__lt=end_date
        ).count()

        churned_total = cancelled_count + expired_count

        if starting_active == 0:
            churn_rate = 0.0
        else:
            churn_rate = round((churned_total / starting_active) * 100, 2)

        return {
            "starting_active": starting_active,
            "cancelled": cancelled_count,
            "expired": expired_count,
            "churned_total": churned_total,
            "churn_rate": churn_rate,
        }

    def get(self, request):
        now = timezone.now()
        current_month_start = start_of_month(now)
        next_month_start = add_months(current_month_start, 1)
        last_month_start = add_months(current_month_start, -1)

        current_data = self._period_churn_data(current_month_start, next_month_start)
        previous_data = self._period_churn_data(last_month_start, current_month_start)

        total_change_pct, total_change_direction = percentage_change(
            current_data["churn_rate"],
            previous_data["churn_rate"]
        )

        snapshot_cancelled = Subscription.objects.filter(
            status=SubscriptionStatus.CANCELLED
        ).count()

        snapshot_expired = Subscription.objects.filter(
            status=SubscriptionStatus.EXPIRED
        ).count()

        trend = []
        for i in range(5, -1, -1):
            month_start = add_months(current_month_start, -i)
            month_end = add_months(month_start, 1)
            month_data = self._period_churn_data(month_start, month_end)

            trend.append({
                "label": month_start.strftime("%b"),
                "year": month_start.year,
                "month": month_start.month,
                "starting_active": month_data["starting_active"],
                "cancelled": month_data["cancelled"],
                "expired": month_data["expired"],
                "churned_total": month_data["churned_total"],
                "churn_rate": month_data["churn_rate"],
            })

        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_data = self._period_churn_data(this_week_start, next_week_start)
        prev_week_data = self._period_churn_data(prev_week_start, this_week_start)

        this_week_pct, this_week_direction = percentage_change(
            this_week_data["churn_rate"],
            prev_week_data["churn_rate"]
        )

        month_before_last_start = add_months(last_month_start, -1)
        month_before_last_data = self._period_churn_data(month_before_last_start, last_month_start)

        last_month_pct, last_month_direction = percentage_change(
            previous_data["churn_rate"],
            month_before_last_data["churn_rate"]
        )

        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_data = self._period_churn_data(last_quarter_start, current_quarter_start)
        prev_quarter_data = self._period_churn_data(prev_quarter_start, last_quarter_start)

        last_quarter_pct, last_quarter_direction = percentage_change(
            last_quarter_data["churn_rate"],
            prev_quarter_data["churn_rate"]
        )

        return Response({
            "status": "success",
            "metric": "churn_rate",
            "card": {
                "title": "Churn Rate",
                "value": current_data["churn_rate"],
                "unit": "%",
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month",
                "starting_active": current_data["starting_active"],
                "cancelled_this_period": current_data["cancelled"],
                "expired_this_period": current_data["expired"],
                "churned_total_this_period": current_data["churned_total"],
                "snapshot_cancelled": snapshot_cancelled,
                "snapshot_expired": snapshot_expired
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": this_week_data["churn_rate"],
                    "unit": "%",
                    "starting_active": this_week_data["starting_active"],
                    "cancelled": this_week_data["cancelled"],
                    "expired": this_week_data["expired"],
                    "churned_total": this_week_data["churned_total"],
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": current_data["churn_rate"],
                    "unit": "%",
                    "starting_active": current_data["starting_active"],
                    "cancelled": current_data["cancelled"],
                    "expired": current_data["expired"],
                    "churned_total": current_data["churned_total"],
                    "change_percentage": total_change_pct,
                    "change_direction": total_change_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": previous_data["churn_rate"],
                    "unit": "%",
                    "starting_active": previous_data["starting_active"],
                    "cancelled": previous_data["cancelled"],
                    "expired": previous_data["expired"],
                    "churned_total": previous_data["churned_total"],
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": last_quarter_data["churn_rate"],
                    "unit": "%",
                    "starting_active": last_quarter_data["starting_active"],
                    "cancelled": last_quarter_data["cancelled"],
                    "expired": last_quarter_data["expired"],
                    "churned_total": last_quarter_data["churned_total"],
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)


# subscription revenue
class AdminSubscriptionRevenueAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def _period_revenue(self, start_date, end_date):
        total = Subscription.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED]
        ).aggregate(
            total=Coalesce(Sum("plan__price", output_field=DecimalField(max_digits=12, decimal_places=2)), Decimal("0.00"))
        )["total"]
        return float(total or 0.0)

    def get(self, request):
        now = timezone.now()
        current_month_start = start_of_month(now)
        next_month_start = add_months(current_month_start, 1)
        last_month_start = add_months(current_month_start, -1)

        total_revenue = float(
            Subscription.objects.aggregate(
                total=Coalesce(Sum("plan__price", output_field=DecimalField(max_digits=12, decimal_places=2)), Decimal("0.00"))
            )["total"] or 0.0
        )

        current_value = self._period_revenue(current_month_start, next_month_start)
        previous_value = self._period_revenue(last_month_start, current_month_start)

        total_change_pct, total_change_direction = percentage_change(current_value, previous_value)

        trend = []
        for i in range(5, -1, -1):
            month_start = add_months(current_month_start, -i)
            month_end = add_months(month_start, 1)

            revenue = self._period_revenue(month_start, month_end)

            trend.append({
                "label": month_start.strftime("%b"),
                "year": month_start.year,
                "month": month_start.month,
                "subscription_revenue": revenue
            })

        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_value = self._period_revenue(this_week_start, next_week_start)
        prev_week_value = self._period_revenue(prev_week_start, this_week_start)
        this_week_pct, this_week_direction = percentage_change(this_week_value, prev_week_value)

        this_month_value = current_value
        last_month_value = previous_value
        this_month_pct, this_month_direction = percentage_change(this_month_value, last_month_value)

        month_before_last_start = add_months(last_month_start, -1)
        month_before_last_value = self._period_revenue(month_before_last_start, last_month_start)
        last_month_pct, last_month_direction = percentage_change(last_month_value, month_before_last_value)

        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_value = self._period_revenue(last_quarter_start, current_quarter_start)
        prev_quarter_value = self._period_revenue(prev_quarter_start, last_quarter_start)
        last_quarter_pct, last_quarter_direction = percentage_change(last_quarter_value, prev_quarter_value)

        return Response({
            "status": "success",
            "metric": "subscription_revenue",
            "card": {
                "title": "Subscription Revenue",
                "value": round(total_revenue, 2),
                "currency": "USD",
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month"
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": round(this_week_value, 2),
                    "currency": "USD",
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": round(this_month_value, 2),
                    "currency": "USD",
                    "change_percentage": this_month_pct,
                    "change_direction": this_month_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": round(last_month_value, 2),
                    "currency": "USD",
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": round(last_quarter_value, 2),
                    "currency": "USD",
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)
    

# stripe 2 percentage fees
from decimal import Decimal
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from jobs.models import Job
from payments.enums import PaymentStatus


class AdminStripeFeeRevenueAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def _period_fee_revenue(self, start_date, end_date):
        total_job_amount = Job.objects.filter(
            payment_status=PaymentStatus.PAID,
            scheduled_date__gte=start_date.date(),
            scheduled_date__lt=end_date.date()
        ).aggregate(
            total=Coalesce(
                Sum("total_price"),  # ✅ FIXED HERE
                Decimal("0.00")
            )
        )["total"] or Decimal("0.00")

        return float(total_job_amount * Decimal("0.02"))

    def get(self, request):
        now = timezone.now()

        # ------------------ MONTHS ------------------
        def start_of_month(dt):
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        def add_months(source_date, months):
            month = source_date.month - 1 + months
            year = source_date.year + month // 12
            month = month % 12 + 1
            return source_date.replace(year=year, month=month, day=1)

        current_month_start = start_of_month(now)
        next_month_start = add_months(current_month_start, 1)
        last_month_start = add_months(current_month_start, -1)

        # ------------------ TOTAL ------------------
        total_job_amount = Job.objects.filter(
            payment_status=PaymentStatus.PAID
        ).aggregate(
            total=Coalesce(
                Sum("total_price"),  # ✅ FIXED HERE
                Decimal("0.00")
            )
        )["total"] or Decimal("0.00")

        total_fee_revenue = float(total_job_amount * Decimal("0.02"))

        # ------------------ CURRENT / PREVIOUS ------------------
        current_value = self._period_fee_revenue(current_month_start, next_month_start)
        previous_value = self._period_fee_revenue(last_month_start, current_month_start)

        def percentage_change(current, previous):
            if previous == 0:
                return 100.0, "up"
            change = ((current - previous) / previous) * 100
            return round(change, 2), "up" if change >= 0 else "down"

        total_change_pct, total_change_direction = percentage_change(current_value, previous_value)

        # ------------------ TREND ------------------
        trend = []
        for i in range(5, -1, -1):
            month_start = add_months(current_month_start, -i)
            month_end = add_months(month_start, 1)

            fee_revenue = self._period_fee_revenue(month_start, month_end)

            trend.append({
                "label": month_start.strftime("%b"),
                "year": month_start.year,
                "month": month_start.month,
                "stripe_fee_revenue": round(fee_revenue, 2)
            })

        # ------------------ WEEK ------------------
        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_week_start = this_week_start + timedelta(days=7)
        prev_week_start = this_week_start - timedelta(days=7)

        this_week_value = self._period_fee_revenue(this_week_start, next_week_start)
        prev_week_value = self._period_fee_revenue(prev_week_start, this_week_start)
        this_week_pct, this_week_direction = percentage_change(this_week_value, prev_week_value)

        # ------------------ MONTH ------------------
        this_month_value = current_value
        last_month_value = previous_value
        this_month_pct, this_month_direction = percentage_change(this_month_value, last_month_value)

        month_before_last_start = add_months(last_month_start, -1)
        month_before_last_value = self._period_fee_revenue(month_before_last_start, last_month_start)
        last_month_pct, last_month_direction = percentage_change(last_month_value, month_before_last_value)

        # ------------------ QUARTER ------------------
        current_quarter = ((now.month - 1) // 3) + 1
        current_quarter_start_month = (current_quarter - 1) * 3 + 1

        current_quarter_start = now.replace(
            month=current_quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        last_quarter_start = add_months(current_quarter_start, -3)
        prev_quarter_start = add_months(current_quarter_start, -6)

        last_quarter_value = self._period_fee_revenue(last_quarter_start, current_quarter_start)
        prev_quarter_value = self._period_fee_revenue(prev_quarter_start, last_quarter_start)
        last_quarter_pct, last_quarter_direction = percentage_change(last_quarter_value, prev_quarter_value)

        # ------------------ RESPONSE ------------------
        return Response({
            "status": "success",
            "metric": "stripe_fee_revenue",
            "card": {
                "title": "2% Stripe Revenue",
                "value": round(total_fee_revenue, 2),
                "currency": "USD",
                "change_percentage": total_change_pct,
                "change_direction": total_change_direction,
                "comparison_label": "vs last month"
            },
            "chart": {
                "type": "line",
                "title": "6-Month Trend",
                "data": trend
            },
            "breakdown": {
                "this_week": {
                    "label": "This Week",
                    "value": round(this_week_value, 2),
                    "currency": "USD",
                    "change_percentage": this_week_pct,
                    "change_direction": this_week_direction,
                    "comparison_label": "vs previous week"
                },
                "this_month": {
                    "label": "This Month",
                    "value": round(this_month_value, 2),
                    "currency": "USD",
                    "change_percentage": this_month_pct,
                    "change_direction": this_month_direction,
                    "comparison_label": "vs last month"
                },
                "last_month": {
                    "label": "Last Month",
                    "value": round(last_month_value, 2),
                    "currency": "USD",
                    "change_percentage": last_month_pct,
                    "change_direction": last_month_direction,
                    "comparison_label": "vs previous month"
                },
                "last_quarter": {
                    "label": "Last Quarter",
                    "value": round(last_quarter_value, 2),
                    "currency": "USD",
                    "change_percentage": last_quarter_pct,
                    "change_direction": last_quarter_direction,
                    "comparison_label": "vs previous quarter"
                }
            }
        }, status=status.HTTP_200_OK)



# recent activity
# activity/views.py

from itertools import chain
from invoice.models import Invoice
from django.contrib.auth import get_user_model
from invoice.models import Invoice
from subscriptions.models import Subscription
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

User = get_user_model()

@api_view(["GET"])
@permission_classes([IsAdminUser])
def recent_activities(request):

    activities = []

    # User signup
    for user in User.objects.order_by("-date_joined")[:20]:
        activities.append({
            "user_name": user.get_full_name() or user.email,
            "action": "User Signup",
            "status": "success",
            "date": user.date_joined,
        })

    # Invoice sent
    for invoice in Invoice.objects.order_by("-created_at")[:20]:
        activities.append({
            "user_name": invoice.sent_to_email,
            "action": "Invoice Sent",
            "status": invoice.status,
            "date": invoice.created_at,
        })

    # Payment completed
    for invoice in Invoice.objects.filter(
        status=Invoice.Status.PAID
    ).order_by("-paid_at")[:20]:
        activities.append({
            "user_name": invoice.sent_to_email,
            "action": "Payment Completed",
            "status": "paid",
            "date": invoice.paid_at,
        })

    activities.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    return Response(activities[:20])