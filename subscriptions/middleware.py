from django.utils import timezone
from django.http import JsonResponse
from .models import Subscription


class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            sub = Subscription.objects.filter(
                user=request.user,
                is_active=True
            ).first()

            if sub:
                now = timezone.now()

                # Trial expired
                if sub.is_trial and now > sub.trial_end_date:
                    sub.is_active = False
                    sub.status = "expired"
                    sub.save(update_fields=["is_active", "status"])

                    return JsonResponse(
                        {"detail": "Trial expired. Please subscribe."},
                        status=403
                    )

                # Paid expired
                if not sub.is_trial and now > sub.end_date:
                    sub.is_active = False
                    sub.status = "expired"
                    sub.save(update_fields=["is_active", "status"])

                    return JsonResponse(
                        {"detail": "Subscription expired."},
                        status=403
                    )

        return self.get_response(request)