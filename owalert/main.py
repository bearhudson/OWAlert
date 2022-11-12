from openweatherclass import OpenWeatherClass
import pushbullet
from time import sleep
from _datetime import datetime
from datetime import timedelta
import requests
import os


API_KEY = os.getenv("API_KEY")
SLEEP = 3600
ZIPCODE = "02188"
COUNTRY_CODE = "us"


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)
        self.town = get_location_name()
        self.request_time = self.owc.weather_data['current']['dt']
        self.request_dt = datetime.fromtimestamp(self.request_time)
        self.expires_dt = self.request_dt + timedelta(hours=1)
        self.pushbullet_obj = pushbullet.API()
        self.pushbullet_obj.set_token(os.environ.get('PUSHBULLET_API'))
        self.is_alerted: bool = False

    def update_expiry(self, expires: float):
        self.expires_dt = datetime.fromtimestamp(expires)

    def send_push_notify(self, title: str, message: str):
        self.pushbullet_obj.send_note(title, message)
        self.is_alerted = True


def main():
    owalert = OWAlertClass(api_key=API_KEY, zipcode=ZIPCODE, units='metric')
    while True:
        hourly_weather = owalert.owc.weather_data['hourly']
        if 'alerts' in owalert.owc.weather_data and owalert.is_alerted is False:
            description_title = owalert.owc.weather_data['alerts'][0]['event']
            owalert.update_expiry(owalert.owc.weather_data['alerts'][0]['end'])
            owalert.send_push_notify(f"{description_title}", f"in {owalert.town} "
                                     f"Expires: {datetime.strftime(owalert.expires_dt, '%HH')}")
        else:
            for hour in hourly_weather[1:2]:
                for status in hour['weather']:
                    cur_code = int(status['id'])
                    if cur_code < 800 and owalert.is_alerted is False:
                        ending = precip_check(hourly_weather)
                        owalert.update_expiry(ending)
                        owalert.send_push_notify(f"{str.title(owalert.owc.check_condition(cur_code))} in "
                                                 f"{owalert.town}",
                                                 f"Ending~ {datetime.strftime(owalert.expires_dt, '%HH')}")
        sleep(SLEEP)
        owalert.owc.update_weather()
        if owalert.expires_dt < owalert.request_dt:
            owalert.is_alerted = False


def get_location_name() -> str:
    location = requests.get(f"https://nominatim.openstreetmap.org/search?postalcode={ZIPCODE}&"
                            f"format=json&addressdetails=1&country={COUNTRY_CODE}")
    location.raise_for_status()
    location_json = location.json()
    location_str = location_json[-1]['display_name'].split(',')
    return location_str[0]


def precip_check(weather_slice: list) -> int:
    until = weather_slice[0]['dt']
    for hour in weather_slice:
        if hour['weather'][0]['id'] <= 800:
            until = hour['dt']
        else:
            break
    return until


if __name__ == "__main__":
    main()
