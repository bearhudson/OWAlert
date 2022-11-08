from openweatherclass import OpenWeatherClass
from time import sleep
import requests
import os

API_KEY = os.getenv("API_KEY")

while True:
    weather = OpenWeatherClass(api_key=API_KEY, zipcode='02188', units='imperial')
    print(weather.geo_data['name'])
    print(weather.weather_data['current']['temp'])
    print(weather.check_condition(weather.weather_data['current']['weather'][0]['id']))
    sleep(1)