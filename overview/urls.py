from django.urls import path
from .views import (
    AdminTotalClientsAnalyticsView,
    AdminTotalLandscapersAnalyticsView,
    AdminActiveBasicSubscriptionsAnalyticsView,
    AdminActiveProSubscriptionsAnalyticsView,
    AdminJobsCompletedAnalyticsView,
    AdminTotalUsersAnalyticsView,
    AdminChurnRateAnalyticsView,
    AdminSubscriptionRevenueAnalyticsView,
    AdminStripeFeeRevenueAnalyticsView

)

urlpatterns = [
    path("admin/analytics/total-users/",AdminTotalUsersAnalyticsView.as_view(),name="admin-total-users-analytics" ),
    path("admin/analytics/total-clients/", AdminTotalClientsAnalyticsView.as_view(), name="admin-total-clients-analytics"),
    path("admin/analytics/total-landscapers/", AdminTotalLandscapersAnalyticsView.as_view(), name="admin-total-landscapers-analytics"),
    path("admin/analytics/active-basic-subscriptions/", AdminActiveBasicSubscriptionsAnalyticsView.as_view(), name="admin-active-basic-subscriptions-analytics"),
    path("admin/analytics/active-pro-subscriptions/", AdminActiveProSubscriptionsAnalyticsView.as_view(), name="admin-active-pro-subscriptions-analytics"),
    path("admin/analytics/jobs-completed/", AdminJobsCompletedAnalyticsView.as_view(), name="admin-jobs-completed-analytics"),
    path("admin/analytics/churn-rate/", AdminChurnRateAnalyticsView.as_view(), name="admin-churn-rate-analytics"),
    path("admin/analytics/subscription-revenue/", AdminSubscriptionRevenueAnalyticsView.as_view(), name="admin-subscription-revenue-analytics"),
    path("admin/analytics/stripe-fee-revenue/", AdminStripeFeeRevenueAnalyticsView.as_view(), name="admin-stripe-fee-revenue-analytics"),
]