from .models import Subscription, SubscriptionStatus


def get_user_plan(user):
    """
    Returns active plan name for a user
    """
    subscription = (
        Subscription.objects
        .filter(user=user, status=SubscriptionStatus.ACTIVE, is_active=True)
        .select_related("plan")
        .first()
    )

    if not subscription:
        return "Basic"

    return subscription.plan.name