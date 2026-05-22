# subscriptions/helpers.py

from subscriptions.models import Subscription
from invitations.models import TeamInvitation, InvitationStatus

from django.db.models import Q
from connections.models import ConnectionRequest


def get_active_client_count(landscaper_user):

    return ConnectionRequest.objects.filter(
        is_accepted=True
    ).filter(
        Q(sender=landscaper_user) | Q(receiver=landscaper_user)
    ).count()

# =========================================
# GET ACTIVE SUBSCRIPTION
# =========================================

def get_active_subscription(user):

    subscription = Subscription.objects.filter(
        user=user,   # ✅ FIXED (was landscaper)
        is_active=True
    ).select_related("plan").first()

    return subscription


# =========================================
# GET PLAN NAME
# =========================================

def get_plan_name(user):

    subscription = get_active_subscription(user)

    if not subscription:
        return None

    return subscription.plan.name.lower()


# =========================================
# CHECK BASIC PLAN
# =========================================

def is_basic_plan(user):

    return get_plan_name(user) == "basic"


# =========================================
# CHECK PRO PLAN
# =========================================

def is_pro_plan(user):

    return get_plan_name(user) == "pro"


# =========================================
# TEAM USER LIMIT
# =========================================



def can_add_team_member(user):

    landscaper = getattr(user, "landscaper_profile", None)
    if not landscaper:
        return False

    plan = get_plan_name(user)

    # -----------------------------
    # COUNT ONLY ACCEPTED WORKERS
    # -----------------------------
    active_workers = TeamInvitation.objects.filter(
        landscaper=landscaper,
        status=InvitationStatus.ACCEPTED
    ).count()

    # BASIC PLAN LIMIT
    if plan == "basic":
        return active_workers <= 1

    # PRO PLAN LIMIT
    elif plan == "pro":
        return active_workers <= 5

    return False


# =========================================
# CLIENT LIMIT
# =========================================


def can_add_client(user):

    landscaper = getattr(user, "landscaper_profile", None)

    if not landscaper:
        return False

    plan = get_plan_name(user)

    total_clients = landscaper.connections.count()

    if plan == "basic":
        return total_clients <= 10

    if plan == "pro":
        return True

    return False


def get_landscaper_plan(user):
    subscription = Subscription.objects.filter(
        user=user,
        is_active=True
    ).select_related("plan").first()

    if not subscription:
        return "basic"

    return subscription.plan.name.lower()

# =========================================
# FEATURES
# =========================================

def can_use_stripe(user):
    return is_pro_plan(user)


def can_use_analytics(user):
    return is_pro_plan(user)


def can_use_white_label(user):
    return is_pro_plan(user)


def can_use_route_optimization(user):
    return is_pro_plan(user)


def can_use_quickbooks(user):
    return is_pro_plan(user)


def can_use_pro_features(user):
    return get_landscaper_plan(user) == "pro"