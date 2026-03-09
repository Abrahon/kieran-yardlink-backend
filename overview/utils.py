from datetime import timedelta
from calendar import monthrange

from django.utils import timezone
from datetime import timedelta
from calendar import monthrange
from decimal import Decimal

from django.utils import timezone


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



# for churn rate revenue helper 

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