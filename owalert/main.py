from time import sleep
from _datetime import datetime
from datetime import timedelta
import requests
import os
import re

from pyzipcode import ZipCodeDatabase
from pushsafer import Client
from openweatherclass import OpenWeatherClass

OW_API_KEY = os.getenv("OW_API_KEY")
PUSHSAFER_API = os.getenv("PUSHSAFER_API")
PUSHSAFER_DEVICE = os.getenv("PUSHSAFER_DEVICE")
ZIPCODE = os.getenv("ZIPCODE")
COUNTRY_CODE = os.getenv("COUNTRY_CODE")
UNITS = os.getenv("UNITS")
SLEEP = 1800


def get_temp_string() -> str:
    if UNITS == 'metric':
        return "°C"
    if UNITS == 'imperial':
        return "°F"

def get_wind_speed() -> str:
    if UNITS == 'metric':
        return "kph"
    if UNITS == 'imperial':
        return "mph"

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

def get_condition_icon(code) -> int:
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

def get_cardinal_direction(degree: float) -> str:
    if degree > 337.5 or degree <= 22.5:
        return "N"
    elif 22.5 < degree <= 67.5:
        return "NE"
    elif 67.5 < degree <= 112.5:
        return "E"
    elif 112.5 < degree <= 157.5:
        return "SE"
    elif 157.5 < degree <= 202.5:
        return "S"
    elif 202.5 < degree <= 247.5:
        return "SW"
    elif 247.5 < degree <= 292.5:
        return "W"
    elif 292.5 < degree <= 337.5:
        return "NW"


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)
        self.town = get_location_name()
        self.request_dt_utc = datetime.fromtimestamp(self.owc.weather_data['current']['dt'])
        self.alert_expires_dt = self.request_dt_utc + timedelta(hours=1)
        self.notify_expires_dt = self.request_dt_utc + timedelta(hours=1)
        self.pushsafer_client = Client(PUSHSAFER_API)
        self.pushsafer_device = PUSHSAFER_DEVICE
        self.is_alerted: bool = False
        self.is_notified: bool = False
        self.zcdb = ZipCodeDatabase()
        self.tz_offset = self.zcdb[ZIPCODE].timezone

    def update_expiry(self, notify_type: str, expires: float):
        if notify_type == 'alert':
            self.alert_expires_dt = datetime.fromtimestamp(expires)
        if notify_type == 'notify':
            self.notify_expires_dt = datetime.fromtimestamp(expires)

    def send_push_notify(self, title: str,
                         message: str,
                         msg_sound: int,
                         icon_type: int,
                         vibration: int = 2,
                         url: str = "",
                         urltitle: str = "",
                         ttl: int = 43200,
                         priority: int = 2,
                         retry: int = 0,
                         expire: int = 0,
                         answer: int = 0):
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
    owalert = OWAlertClass(api_key=OW_API_KEY, zipcode=ZIPCODE, units=UNITS)
    # owalert.send_push_notify("Starting!", "Starting Daemon.", 24, 148)
    while True:
        hourly_weather = owalert.owc.weather_data['hourly']
        print(f"Report for: {datetime.strftime(owalert.request_dt_utc , '%a %b/%d %H:%M')}")
        temp = owalert.owc.weather_data['current']['temp']
        feels_like = owalert.owc.weather_data['current']['feels_like']
        wind_speed = owalert.owc.weather_data['current']['wind_speed']
        wind_direction = get_cardinal_direction(owalert.owc.weather_data['current']['wind_deg'])
        if owalert.alert_expires_dt < owalert.request_dt_utc:
            print("Alert Expired...")
            owalert.is_alerted = False
        if owalert.notify_expires_dt < owalert.request_dt_utc:
            print("Notification Expired...")
            owalert.is_alerted = False
        if 'alerts' in owalert.owc.weather_data and owalert.is_alerted is False:
            description_title = owalert.owc.weather_data['alerts'][0]['event']
            alert_sender_name = owalert.owc.weather_data['alerts'][0]['sender_name']
            alert_expire = owalert.owc.weather_data['alerts'][0]['end']
            owalert.update_expiry(notify_type='alert', expires=alert_expire)
            description = re.sub("\n", " ", owalert.owc.weather_data['alerts'][0]['description'])
            alert_count = len(owalert.owc.weather_data['alerts'])
            print(f"{description_title} from {alert_sender_name} in {owalert.town} "
                  f"Expires: {datetime.strftime(owalert.alert_expires_dt, '%a %b/%d %H:%M')}")
            owalert.send_push_notify(f"{description_title} from {alert_sender_name}",
                                     f"in {owalert.town} \n"
                                     f"Expires: {datetime.strftime(owalert.alert_expires_dt, '%a %b/%d %H:%M')}\n"
                                     f"Alert Count: {alert_count}\n"
                                     f"Currently: Temp: {temp}{get_temp_string()} "
                                     f"Feels like: {feels_like}{get_temp_string()}\n"
                                     f"Wind Speed: {wind_speed} {get_wind_speed()} "
                                     f"Wind Direction: {wind_direction}\n"
                                     f"{description}",
                                     24, # Radio Tuner
                                     148) # "!" Icon
            owalert.is_alerted = True
        if not owalert.is_notified:
            print("Checking Precip...")
            cur_code = owalert.owc.weather_data['current']['weather'][0]['id']
            if cur_code < 800 and not owalert.is_notified:
                for condition in owalert.owc.weather_data['current']['weather']:
                    if condition['main'] == 'Rain':
                        print("Prepping notification...")
                        print(cur_code, owalert.is_notified)
                        owalert.update_expiry(notify_type='notify', expires=precip_check(hourly_weather))
                        notify_expire = owalert.notify_expires_dt + timedelta(hours=owalert.tz_offset)
                        rain_rate = owalert.owc.weather_data['current']['rain']['1h']
                        print("Sending rain notification...")
                        owalert.send_push_notify("Rain Alert",
                                                 f"{str.title(owalert.owc.check_condition(cur_code))} "
                                                 f"in {owalert.town} \n"
                                                 f"Expires: {datetime.strftime(notify_expire, '%a %b/%d %H:%M')}\n"
                                                 # f"Precipitation: {precip_prob}\n"
                                                 f"Rate: {rain_rate}/hr\n"
                                                 f"Currently: Temp: {temp}{get_temp_string()} "
                                                 f"Feels like: {feels_like}{get_temp_string()}\n"
                                                 f"Wind Speed: {wind_speed} {get_wind_speed()} "
                                                 f"Wind Direction: {wind_direction}\n",
                                                 22,  # Morse Sound
                                                 get_condition_icon(cur_code))
                        owalert.is_notified = True
                    if condition['main'] == 'Snow':
                        print("Prepping notification...")
                        print(cur_code, owalert.is_notified)
                        owalert.update_expiry(notify_type='notify', expires=precip_check(hourly_weather))
                        notify_expire = owalert.notify_expires_dt + timedelta(hours=owalert.tz_offset)
                        snow_rate = owalert.owc.weather_data['current']['snow']['1h']
                        print("Sending snow notification...")
                        owalert.send_push_notify("Snow Alert",
                                                 f"{str.title(owalert.owc.check_condition(cur_code))} "
                                                 f"in {owalert.town} \n"
                                                 f"Expires: {datetime.strftime(notify_expire, '%a %b/%d %H:%M')}\n"
                                                 # f"Precipitation: {precip_prob}\n"
                                                 f"Rate: {snow_rate}/hr\n"
                                                 f"Currently: Temp: {temp}{get_temp_string()} "
                                                 f"Feels like: {feels_like}{get_temp_string()}\n"
                                                 f"Wind Speed: {wind_speed} {get_wind_speed()} "
                                                 f"Wind Direction: {wind_direction}\n",
                                                 22,  # Morse Sound
                                                 get_condition_icon(cur_code))
                        owalert.is_notified = True
        print("Sleeping...")
        sleep(SLEEP)
        owalert.update_data()


if __name__ == "__main__":
    main()
