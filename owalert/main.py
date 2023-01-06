from time import sleep
from _datetime import datetime
from datetime import timedelta
import requests
import os

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


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)
        self.town = get_location_name()
        self.request_time = self.owc.weather_data['current']['dt']
        self.request_dt = datetime.fromtimestamp(self.request_time)
        self.alert_expires_dt = self.request_dt + timedelta(hours=1)
        self.notify_expires_dt = self.request_dt + timedelta(hours=1)
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
    owalert = OWAlertClass(api_key=OW_API_KEY, zipcode=ZIPCODE, units='imperial')
    # owalert.send_push_notify("Starting!", "Starting Daemon.", 24, 148)
    while True:
        hourly_weather = owalert.owc.weather_data['hourly']
        report_time = datetime.fromtimestamp(hourly_weather[0]['dt']) + timedelta(hours=owalert.tz_offset)
        print(f"Report for: {datetime.strftime(report_time, '%a %b/%d %H:%M')}")
        if owalert.alert_expires_dt < owalert.request_dt:
            print("Alert Expired...")
            owalert.is_alerted = False
        if owalert.notify_expires_dt < owalert.request_dt:
            print("Notification Expired...")
            owalert.is_alerted = False
        if 'alerts' in owalert.owc.weather_data and owalert.is_alerted is False:
            description_title = owalert.owc.weather_data['alerts'][0]['event']
            description = owalert.owc.weather_data['alerts'][0]['description']
            alert_count = len(owalert.owc.weather_data['alerts'])
            owalert.update_expiry(notify_type='alert', expires=owalert.owc.weather_data['alerts'][0]['end'])
            alert_expire = owalert.alert_expires_dt + timedelta(hours=owalert.tz_offset)
            print(f"{description_title}", f"in {owalert.town} "
                                          f"Expires: {datetime.strftime(owalert.alert_expires_dt, '%a %b/%d %H:%M')}")
            owalert.send_push_notify(f"{description_title}",
                                     f"in {owalert.town} \n"
                                     f"Expires {datetime.strftime(alert_expire, '%a %b/%d %H:%M')}\n"
                                     f"Alert Count {alert_count}\n"
                                     f"{description}",
                                     24, # Radio Tuner
                                     148) # "!" Icon
            owalert.is_alerted = True
        if not owalert.is_notified:
            print("Checking Precip...")
            cur_code = owalert.owc.weather_data['current']['weather'][0]['id']
            if cur_code < 800 and not owalert.is_notified:
                for status in owalert.owc.weather_data['current']:
                    if cur_code < 800 and owalert.is_notified == False:
                        print("Prepping notification...")
                        print(cur_code, owalert.is_notified)
                        owalert.update_expiry(notify_type='notify', expires=precip_check(hourly_weather))
                        notify_expire = owalert.notify_expires_dt + timedelta(hours=owalert.tz_offset)
                        if status == 'rain':
                            rain_rate = status['rain']['1h']
                        else:
                            rain_rate = 0
                        print("Sending rain notification...")
                        owalert.send_push_notify("Rain Alert",
                                                 f"{str.title(owalert.owc.check_condition(cur_code))} "
                                                 f"in {owalert.town} \n"
                                                 f"Date: {datetime.strftime(notify_expire, '%a %b/%d %H:%M')}\n"
                                                 # f"Precipitation: {precip_prob}\n"
                                                 f"Rate: {rain_rate}\n",
                                                 22,  # Morse Sound
                                                 get_condition_icon(cur_code))
                        owalert.is_notified = True
                    if status == 'snow' and cur_code < 800:
                        print("Prepping notification...")
                        print(cur_code, owalert.is_notified)
                        owalert.update_expiry(notify_type='notify', expires=precip_check(hourly_weather))
                        notify_expire = owalert.notify_expires_dt + timedelta(hours=owalert.tz_offset)
                        snow_rate = status['snow']['1h']
                        print("Sending snow notification...")
                        owalert.send_push_notify("Snow Alert",
                                                 f"{str.title(owalert.owc.check_condition(cur_code))} "
                                                 f"in {owalert.town} \n"
                                                 f"Date: {datetime.strftime(notify_expire, '%a %b/%d %H:%M')}\n"
                                                 # f"Precipitation: {precip_prob}\n"
                                                 f"Rate: {snow_rate}\n",
                                                 22,  # Morse Sound
                                                 get_condition_icon(cur_code))
                        owalert.is_notified = True
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


if __name__ == "__main__":
    main()
