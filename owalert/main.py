from time import sleep
from _datetime import datetime
from datetime import timedelta
import requests
import os

from pushsafer import Client
from openweatherclass import OpenWeatherClass

OW_API_KEY = os.getenv("OW_API_KEY")
PUSH_API = os.getenv("PUSHBULLET_API")
PUSHSAFER_API = os.getenv("PUSHSAFER_API")
PUSHSAFER_DEVICE = os.getenv("PUSHSAFER_DEVICE")
ZIPCODE = os.getenv("ZIPCODE")
COUNTRY_CODE = os.getenv("COUNTRY_CODE")
UNITS = os.getenv("UNITS")
SLEEP = 1800


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)
        self.town = get_location_name()
        self.request_time = self.owc.weather_data['current']['dt']
        self.request_dt = datetime.fromtimestamp(self.request_time)
        self.expires_dt = self.request_dt + timedelta(hours=1)
        self.pushsafer_client = Client(PUSHSAFER_API)
        self.pushsafer_device = PUSHSAFER_DEVICE
        self.is_alerted: bool = False
        self.is_notified: bool = False

    def update_expiry(self, expires: float):
        self.expires_dt = datetime.fromtimestamp(expires)

    def send_push_notify(self, title: str, message: str, msg_sound: int, icon_type: int, vibration: int = 2,
                         url: str = "", urltitle: str = "", ttl: int = 43200, priority: int = 2, retry: int = 0,
                         expire: int = 0, answer: int = 0):
        self.pushsafer_client.send_message(f"{message}",
                                           f"{title}",
                                           f"{self.pushsafer_device}",
                                           f"{icon_type}",
                                           f"{msg_sound}",
                                           f"{vibration}",
                                           f"{url}",
                                           f"{urltitle}",
                                           f"{ttl}",
                                           f"{priority}",
                                           f"{retry}",
                                           f"{expire}",
                                           f"{answer}",
                                           "", "", "")

    def update_data(self):
        self.owc.get_weather()
        self.request_time = self.owc.weather_data['current']['dt']
        self.request_dt = datetime.fromtimestamp(self.request_time)


def main():
    owalert = OWAlertClass(api_key=OW_API_KEY, zipcode=ZIPCODE, units='imperial')
    while True:
        hourly_weather = owalert.owc.weather_data['hourly']
        print(f"Report for: {datetime.strftime(datetime.fromtimestamp(hourly_weather[0]['dt']), '%H%M')}")
        if owalert.expires_dt < owalert.request_dt:
            print("Alert Expired...")
            owalert.is_alerted = False
        if 'alerts' in owalert.owc.weather_data and owalert.is_alerted is False:
            description_title = owalert.owc.weather_data['alerts'][0]['event']
            owalert.update_expiry(owalert.owc.weather_data['alerts'][0]['end'])
            print(f"{description_title}", f"in {owalert.town} "
                                          f"Expires: {datetime.strftime(owalert.expires_dt, '%m/%d:%H')}")
            owalert.send_push_notify(f"{description_title}", f"in {owalert.town} "
                                                             f"Expires: {datetime.strftime(owalert.expires_dt, '%H')}",
                                     24, 64)
        else:
            print("No Alerts. Checking Precip...")
            for hour in hourly_weather[1:2]:
                for status in hour['weather']:
                    cur_code = int(status['id'])
                    print(cur_code, owalert.is_notified)
                    if cur_code < 800 and owalert.is_notified is False:
                        print("Prepping notification...")
                        rain_rate = None
                        snow_rate = None
                        if 'rain' in hour:
                            rain_rate = hour['rain']['1h']
                        if 'snow' in hour:
                            snow_rate = hour['snow']['1h']
                        duration = precip_check(hourly_weather)
                        owalert.update_expiry(duration)
                        precip_prob = hour['pop'] = 0
                        if rain_rate:
                            print("Sending notification...")
                            owalert.send_push_notify("Rain Alert", 
                                                     f"{str.title(owalert.owc.check_condition(cur_code))} "
                                                     f"in {owalert.town} "
                                                     f"D:{datetime.strftime(owalert.expires_dt, '%HH')} "
                                                     f"P:{precip_prob} R:{rain_rate}",
                                                     22, # Morse Sound
                                                     get_condition_icon(cur_code))
                        if snow_rate:
                            print("Sending notification...")
                            owalert.send_push_notify("Snow Alert",
                                                     f"{str.title(owalert.owc.check_condition(cur_code))} "
                                                     f"in {owalert.town} "
                                                     f"D:{datetime.strftime(owalert.expires_dt, '%HH')} "
                                                     f"P:{precip_prob} R:{snow_rate}",
                                                     22,  # Morse Sound
                                                     get_condition_icon(cur_code))
        print("Sleeping...")
        sleep(SLEEP)
        owalert.update_data()


def get_location_name() -> str:
    location = requests.get(f"https://nominatim.openstreetmap.org/search?postalcode={ZIPCODE}&"
                            f"format=json&addressdetails=1&country={COUNTRY_CODE}")
    location.raise_for_status()
    location_json = location.json()
    location_str = location_json[-1]['display_name'].split(',')
    return location_str[0]


def precip_check(weather_slice: list) -> int:
    duration = weather_slice[0]['dt']
    for hour in weather_slice:
        if hour['weather'][0]['id'] <= 800:
            duration = hour['dt']
        else:
            break
    return duration

def get_condition_icon(code):
    thunder_code = range(200, 230)
    thunder_icon = 68
    rain_code = range(300, 531)
    rain_icon = 67
    snow_code = range(600, 622)
    snow_icon = 76
    fog_code = range(701, 741)
    fog_icon = 66
    extreme_code = range(751, 781)
    extreme_icon = 69
    clear_icon = 64
    cloud_code = range(801, 804)
    cloud_icon = 65
    if code in thunder_code:
        return thunder_icon
    if code in rain_code:
        return rain_icon
    if code in snow_code:
        return snow_icon
    if code in fog_code:
        return fog_icon
    if code in extreme_code:
        return extreme_icon
    if code in cloud_code:
        return cloud_icon
    if code == 800:
        return clear_icon


if __name__ == "__main__":
    main()
