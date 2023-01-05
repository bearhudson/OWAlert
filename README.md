### OWAlerter

##### A container application that sends push weather alerts to [Pushbullet](https://www.pushbullet.com/)

###### Requirements
* OpenWeather [API key](https://openweathermap.org/appid)
* Pushsafer [API key](https://www.pushsafer.com/en/pushapi)
* Pushsafer Device ID [Device/Group IDs](https://www.pushsafer.com/en/pushapi_ext#API-D)

###### Environment Variables

* OW_API_KEY - OpenWeather API Key
* PUSHSAFER_API = Pushsafer API Key
* PUSHSAFER_DEVICE = Pushsafer Device/Group
* ZIPCODE = Your Zipcode
* COUNTRY_CODE = Two-letter country code. e.g. _**us**_
* UNITS = _**imperial**_ vs. _**metric**_

###### Runtime Notes

* You can setup environment variables and envoke main.py after building the Poetry virtual environment
    ```bash
    $ poetry install
    $ .venv/bin/python3 owawlert/main.py
    ```
* I have also created a Dockerfile and docker.sh^ to build and launch a local instance which reads the environment variables from a .env file you will need to create. The format for is VARIABLE=VALUE
    ```bash
    $ ./docker.sh
    ```
    ^ Script requires rootless docker.