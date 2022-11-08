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
    owalert_object = OWAlertClass(api_key=API_KEY, zipcode='92065', units='metric')
    while True:
        hourly_weather = owalert_object.owc.weather_data['hourly']
        for hour in hourly_weather[1:2]:
            for status in hour['weather']:
                cur_code = int(status['id'])
                if cur_code <= 622:
                    print(owalert_object.owc.check_condition(cur_code))
                    print(datetime.strftime(datetime.fromtimestamp(hour['dt']), '%H:%M'))
            if 'alerts' in hour:
                print(hour['alerts'])
        sleep(SLEEP)
        owalert_object.owc.update_weather()


if __name__ == "__main__":
    main()
