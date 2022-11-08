from openweatherclass import OpenWeatherClass
from time import sleep
import os

API_KEY = os.getenv("API_KEY")
SLEEP = 3600


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)


def main():
    owalert_object = OWAlertClass(api_key=API_KEY, zipcode='02188', units='imperial')
    while True:
        hourly_weather = owalert_object.owc.weather_data['hourly']
        for hour in hourly_weather:
            if 'alerts' in hour:
                print(hour)
        sleep(SLEEP)
        owalert_object.owc.update_weather()


if __name__ == "__main__":
    main()
