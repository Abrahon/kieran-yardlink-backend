import requests
from django.conf import settings
from django.core.mail import send_mail
from .models import RainAlertSubscription
from datetime import datetime

def check_weather_alert():
    subscriptions = RainAlertSubscription.objects.filter(is_active=True)
    for sub in subscriptions:
        city = sub.city
        api_key = settings.WEATHER_API_KEY
        threshold = settings.RAIN_ALERT_THRESHOLD

        # 5-day forecast
        url_forecast = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
        response = requests.get(url_forecast)
        if response.status_code != 200:
            continue
        forecast_data = response.json()

        # Current weather (temperature and day length)
        url_current = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
        response_current = requests.get(url_current)
        if response_current.status_code != 200:
            continue
        current_data = response_current.json()
        temp = current_data['main']['temp']
        sunrise = current_data['sys']['sunrise']
        sunset = current_data['sys']['sunset']
        day_length_hours = (sunset - sunrise) / 3600

        # Analyze forecast for rain probability
        rain_dates = {}  # date -> list of times with probability
        sunny_days = set()
        for item in forecast_data['list']:
            dt_txt = item['dt_txt']
            dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
            date_only = dt.date()
            weather = item['weather'][0]['main'].lower()
            rain_prob = item.get('pop', 0) * 100  # %

            if 'rain' in weather or rain_prob > 0:
                if rain_prob < threshold:
                    continue  # skip low-probability rain
                if date_only not in rain_dates:
                    rain_dates[date_only] = []
                rain_dates[date_only].append({
                    "time": dt_txt,
                    "probability": rain_prob,
                    "temperature": item['main']['temp'],
                    "weather": item['weather'][0]['main']
                })
            elif 'clear' in weather:
                sunny_days.add(date_only)

        # Send email if rain forecast exists
        if rain_dates:
            message = f"City: {city}\nCurrent Temperature: {temp}°C\nDay Length: {day_length_hours:.1f} hours\n\n"
            message += "Rain Forecast:\n"
            for date, infos in rain_dates.items():
                message += f"{date}:\n"
                for info in infos:
                    message += f" - {info['time']}: {info['weather']}, Temp: {info['temperature']}°C, Rain Chance: {info['probability']}%\n"
            message += f"\nSunny Days in Forecast: {len(sunny_days)}"

            send_mail(
                subject=f"Rain Alert for {city}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sub.user.email],
            )
