
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
import requests
from django.conf import settings
from .models import RainAlertSubscription


class SubscribeRainAlert(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        city = request.data.get("city") or request.user.address
        if not city:
            return Response({"error": "City or user address required"}, status=400)

        sub, _ = RainAlertSubscription.objects.get_or_create(
            user=request.user,
            city=city
        )
        sub.is_active = True
        sub.save()

        return Response({"status": "subscribed", "city": city})


class UnsubscribeRainAlert(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        city = request.data.get("city") or request.user.address
        if not city:
            return Response({"error": "City required"}, status=400)

        updated = RainAlertSubscription.objects.filter(
            user=request.user,
            city=city
        ).update(is_active=False)

        if not updated:
            return Response({"status": "no subscription found"}, status=404)

        return Response({"status": "unsubscribed", "city": city})

class WeatherByDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        city = request.query_params.get("city") or request.user.address or settings.DEFAULT_CITY
        date_str = request.query_params.get("date")
        threshold = settings.RAIN_ALERT_THRESHOLD

        if not date_str:
            return Response({"error": "Provide date in YYYY-MM-DD format"}, status=400)

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format"}, status=400)

        api_key = settings.WEATHER_API_KEY
        url = "https://api.weatherapi.com/v1/forecast.json"

        params = {
            "key": api_key,
            "q": city,
            "days": 3,
            "aqi": "no"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return Response(
                {"error": "Failed to fetch weather data", "details": str(e)},
                status=500
            )

        data = response.json()

        forecast_days = data.get("forecast", {}).get("forecastday", [])
        forecast_day = next((d for d in forecast_days if d["date"] == date_str), None)

        if not forecast_day:
            return Response({"message": "No forecast available for this date"}, status=404)

        hourly = forecast_day.get("hour", [])
        rain_probability = max((h.get("chance_of_rain", 0) for h in hourly), default=0)

        alert = rain_probability >= threshold
        day_info = forecast_day.get("day", {})
        condition = day_info.get("condition", {})
        weather_icon_url = "https:" + condition.get("icon", "")
        weather_text = condition.get("text", "")

        return Response({
            "city": city,
            "date": date_str,
            "temperature_max": day_info.get("maxtemp_c"),
            "temperature_min": day_info.get("mintemp_c"),
            "avg_temperature": day_info.get("avgtemp_c"),
            "humidity": day_info.get("avghumidity"),
            "wind_speed_kph": day_info.get("maxwind_kph"),
            "rain_probability": rain_probability,
            "alert": alert,
            "weather_text": weather_text,
            "weather_icon": weather_icon_url,
            "message": "Rain expected" if alert else "No rain expected"
        })
