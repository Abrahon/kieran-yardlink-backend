import django_rq
from django.core.management.base import BaseCommand
from weather.tasks import check_weather_alert

class Command(BaseCommand):
    help = "Schedule weather alert task"

    def handle(self, *args, **kwargs):
        scheduler = django_rq.get_scheduler('default')
        scheduler.schedule(
            scheduled_time=None,
            func=check_weather_alert,
            interval=900,  # every 15 min
            repeat=None
        )
        self.stdout.write("Weather alert task scheduled every 15 minutes")
