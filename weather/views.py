# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from datetime import datetime
# import requests
# from django.conf import settings
# from .models import RainAlertSubscription


# class SubscribeRainAlert(APIView):
#     permission_classes = [IsAuthenticated]
#     def post(self, request):
#         city = request.data.get('city', settings.DEFAULT_CITY)
#         sub, _ = RainAlertSubscription.objects.get_or_create(user=request.user, city=city)
#         sub.is_active = True
#         sub.save()
#         return Response({"status": "subscribed", "city": city})

# class UnsubscribeRainAlert(APIView):
#     permission_classes = [IsAuthenticated]
#     def post(self, request):
#         city = request.data.get('city', settings.DEFAULT_CITY)
#         try:
#             sub = RainAlertSubscription.objects.get(user=request.user, city=city)
#             sub.is_active = False
#             sub.save()
#             return Response({"status": "unsubscribed", "city": city})
#         except RainAlertSubscription.DoesNotExist:
#             return Response({"status": "no subscription found"})

# class WeatherByDateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         city = request.query_params.get("city", settings.DEFAULT_CITY)
#         date_str = request.query_params.get("date")  # format: YYYY-MM-DD
#         threshold = settings.RAIN_ALERT_THRESHOLD

#         if not date_str:
#             return Response({"error": "Please provide date in YYYY-MM-DD format"}, status=400)
#         try:
#             target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
#         except ValueError:
#             return Response({"error": "Invalid date format"}, status=400)

#         api_key = settings.WEATHER_API_KEY
#         url_forecast = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
#         response = requests.get(url_forecast)
#         if response.status_code != 200:
              
#           return Response({"error": "Failed to fetch weather data"}, status=500)


#         forecast_data = response.json()
#         result = []

#         for item in forecast_data['list']:
#             dt_txt = item['dt_txt']
#             dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
#             if dt.date() == target_date:
#                 rain_prob = item.get('pop', 0) * 100
#                 result.append({
#                     "datetime": dt_txt,
#                     "weather": item['weather'][0]['main'],
#                     "temperature": item['main']['temp'],
#                     "humidity": item['main']['humidity'],       # % humidity
#                     "wind_speed": item['wind']['speed'],       # m/s (convert to km/h later)
#                     "rain_probability": rain_prob
#                 })

#         if not result:
#             return Response({"message": "No forecast available for this date"})

#         # Convert wind speed to km/h
#         for r in result:
#             r['wind_speed'] = round(r['wind_speed'] * 3.6, 2)  # m/s to km/h

#         alert = any(r['rain_probability'] > threshold for r in result)
#         return Response({
#             "city": city,
#             "date": date_str,
#             "forecast": result,
#             "alert": "Rain expected on this day!" if alert else "No rain expected"
#         })
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
        city = request.data.get('city', settings.DEFAULT_CITY)
        sub, _ = RainAlertSubscription.objects.get_or_create(user=request.user, city=city)
        sub.is_active = True
        sub.save()
        return Response({"status": "subscribed", "city": city})


class UnsubscribeRainAlert(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        city = request.data.get('city', settings.DEFAULT_CITY)
        try:
            sub = RainAlertSubscription.objects.get(user=request.user, city=city)
            sub.is_active = False
            sub.save()
            return Response({"status": "unsubscribed", "city": city})
        except RainAlertSubscription.DoesNotExist:
            return Response({"status": "no subscription found"})

class WeatherByDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        city = request.query_params.get("city", settings.DEFAULT_CITY)
        date_str = request.query_params.get("date")  # format: YYYY-MM-DD
        threshold = settings.RAIN_ALERT_THRESHOLD

        if not date_str:
            return Response({"error": "Please provide date in YYYY-MM-DD format"}, status=400)
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format"}, status=400)

        api_key = settings.WEATHER_API_KEY
        url_forecast = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days=3&aqi=no&alerts=yes"
        response = requests.get(url_forecast)

        if response.status_code != 200:
            return Response({"error": "Failed to fetch weather data"}, status=500)

        data = response.json()

        # Find the forecast for the target date
        forecast_day = None
        for day in data.get("forecast", {}).get("forecastday", []):
            if day["date"] == date_str:
                forecast_day = day
                break

        if not forecast_day:
            return Response({"message": "No forecast available for this date"})

        # Use hourly forecast to get accurate rain probability
        hourly_forecast = forecast_day.get("hour", [])
        rain_probability = max(h.get("chance_of_rain", 0) for h in hourly_forecast)

        # Determine if alert should be triggered
        alert = rain_probability > threshold

        day_info = forecast_day.get("day", {})

        result = {
            "city": city,
            "date": date_str,
            "temperature_max": day_info.get("maxtemp_c"),
            "temperature_min": day_info.get("mintemp_c"),
            "avg_temperature": day_info.get("avgtemp_c"),
            "humidity": day_info.get("avghumidity"),
            "wind_speed_kph": day_info.get("maxwind_kph"),
            "rain_probability": rain_probability,
            "alert": "Rain expected on this day!" if alert else "No rain expected"
        }

        return Response(result)
