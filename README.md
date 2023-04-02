### OWAlerter

##### A super simple container application that sends push weather alerts and notications to [Pushsafer](https://www.pushsafer.com/)!

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

* You can setup environment variables and envoke main.py after building the Poetry virtual environment. Timezone data might be incorrect if your system clock is not set to UTC.
    ```bash
    $ poetry install
    $ .venv/bin/python3 owawlert/main.py
    ```
* Docker is the prefered way to run this script. Execute run.sh^ to build and launch a local instance which reads the environment variables from a .env file you will need to create. The format for is 

    ```code
    VARIABLE=VALUE
    ```

    ```bash
    $ ./run.sh
    ```
    ^ Script requires rootless docker.
