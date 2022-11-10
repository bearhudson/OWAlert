from openweatherclass import OpenWeatherClass
from time import sleep
from _datetime import datetime
import os

API_KEY = os.getenv("API_KEY")
SLEEP = 3600


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)
        self.is_alerted: bool = False
        self.last_alerted: datetime


def main():
    owalert_object = OWAlertClass(api_key=API_KEY, zipcode='02188', units='metric')
    while True:
        hourly_weather = owalert_object.owc.weather_data['hourly']
        for hour in hourly_weather[1:2]:
            for status in hour['weather']:
                cur_code = int(status['id'])
                if cur_code <= 622:
                    precip_time = datetime.strftime(datetime.fromtimestamp(hour['dt']), '%H:%M')
                    alert_text = f"Subject: Alert for {owalert_object.owc.zipcode}\n" \
                                 f"Condition: {owalert_object.owc.check_condition(cur_code)}\n" \
                                 f"Starting at: {precip_time}"
                    print(alert_text)
            if 'alerts' in hour:
                print(hour['alerts'])
            else:
                print(f"No alerts at this time. Currently: {str.title(owalert_object.owc.check_condition(cur_code))}")
        sleep(SLEEP)
        owalert_object.owc.update_weather()


if __name__ == "__main__":
    main()
