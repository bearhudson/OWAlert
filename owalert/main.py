from openweatherclass import OpenWeatherClass
import pushbullet
from time import sleep
from _datetime import datetime
from datetime import timedelta
import os


API_KEY = os.getenv("API_KEY")
SLEEP = 3600
ZIPCODE = "02188"


class OWAlertClass:
    def __init__(self, **kwargs):
        self.owc = OpenWeatherClass(**kwargs)
        self.is_alerted: bool = False
        self.request_time = self.owc.weather_data['current']['dt']
        self.request_dt = datetime.fromtimestamp(self.request_time)
        self.expires_dt = self.request_dt + timedelta(hours=1)
        self.email = os.environ.get('MY_EMAIL')
        self.password = os.environ.get('MY_PASSWORD')
        self.my_server = os.environ.get('MY_SERVER')
        self.my_from = os.environ.get('MY_FROM')
        self.pushbullet_obj = pushbullet.API()
        self.pushbullet_obj.set_token(os.environ.get('PUSHBULLET_API'))

    def update_expiry(self, expires: int):
        self.expires_dt = datetime.fromtimestamp(expires)

    def send_push_notify(self, title, message):
        print(self.request_time)
        print(self.request_dt)
        print(self.expires_dt)
        print(self.is_alerted)
        print(message)
        self.pushbullet_obj.send_note(title, message)
        self.is_alerted = True


def main():
    owalert = OWAlertClass(api_key=API_KEY, zipcode=ZIPCODE, units='metric')
    while True:
        hourly_weather = owalert.owc.weather_data['hourly']
        if 'alerts' in owalert.owc.weather_data and owalert.is_alerted is False:
            description_title = owalert.owc.weather_data['alerts'][0]['event']
            description_txt = owalert.owc.weather_data['alerts'][0]['description']
            sender_txt = owalert.owc.weather_data['alerts'][0]['sender_name']
            start_dt = datetime.fromtimestamp(owalert.owc.weather_data['alerts'][0]['start'])
            owalert.update_expiry(owalert.owc.weather_data['alerts'][0]['end'])
            alert_text = f"Subject: Alert! {description_title}\n" \
                         f"Description: From {sender_txt} at {datetime.strftime(owalert.request_dt, '%H:%M')}\n" \
                         f"Start time: {datetime.strftime(start_dt, '%H:%M')} -- " \
                         f"End time: {datetime.strftime(owalert.expires_dt, '%H:%M')}\n" \
                         f"{description_txt}\n"
            owalert.send_push_notify(f"{description_title} for {owalert.owc.zipcode} "
                                     f"Expires: {datetime.strftime(owalert.expires_dt, '%H:%M')}")
        else:
            for hour in hourly_weather[1:2]:
                for status in hour['weather']:
                    cur_code = int(status['id'])
                    if cur_code < 800 and owalert.is_alerted is False:
                        precip_text = f"Subject: Precip. for {owalert.owc.zipcode}\n" \
                                      f"Condition: {owalert.owc.check_condition(cur_code)}\n " \
                                      f"Alert at: {datetime.strftime(owalert.request_dt, '%H:%M')}\n " \
                                      f"Expires at: {datetime.strftime(owalert.expires_dt, '%H:%M')}"
                        owalert.send_push_notify(f"{str.title(owalert.owc.check_condition(cur_code))}",
                                                 f"For: {ZIPCODE} Expires: "
                                                 f"{datetime.strftime(owalert.expires_dt, '%H:%M')}")
        sleep(SLEEP)
        owalert.owc.update_weather()
        if owalert.expires_dt < owalert.request_dt:
            owalert.is_alerted = False


if __name__ == "__main__":
    main()
