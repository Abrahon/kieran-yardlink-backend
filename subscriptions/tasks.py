from celery import shared_task
from django.utils import timezone
from subscriptions.models import Subscription
from subscriptions.enums import SubscriptionStatus


@shared_task
def check_expired_trials():

    expired_trials = Subscription.objects.filter(
        is_trial=True,
        status=SubscriptionStatus.TRIALING,
        end_date__lte=timezone.now()
    )

    for subscription in expired_trials:

        # User disabled auto renew
        if not subscription.auto_renew:

            subscription.status = SubscriptionStatus.EXPIRED
            subscription.is_active = False

            subscription.save(update_fields=[
                "status",
                "is_active",
            ])

        # If auto renew is enabled,
        # DO NOTHING.
        # Stripe will attempt payment and your webhook
        # will update the subscription automatically.