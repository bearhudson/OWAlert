from openweatherclass import OpenWeatherClass
from time import sleep
import os

API_KEY = os.getenv("API_KEY")


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)


def main():
    ow_object = OWAlertClass(api_key=API_KEY, zipcode='02188', units='imperial')
    hourly_weather = ow_object.owc.weather_data['hourly']
    for hour in hourly_weather:
        if 'alerts' in hour:
            print(hour)


if __name__ == "__main__":
    main()

