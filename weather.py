import datetime as dt

from astral.sun import sun
from fmiopendata.wfs import download_stored_query

import settings


class WeatherInfo:
    def __init__(self):
        self.__weatherdict = {
            "temperature": False,
            "pressure": False,
            "humidity": False,
            "windspeed": False,
            "windgust": False,
            "weathersymbol": False
        }

    def get_weather(self):
        timeutc = dt.datetime.utcnow().replace(second=0, microsecond=0)
        timequery = timeutc.isoformat(timespec="seconds") + "Z"
        print(timequery)

        obs = download_stored_query(
            "fmi::forecast::hirlam::surface::point::multipointcoverage",
            args=["place=" + settings.LOCATION,
                  "starttime=" + timequery,
                  "endtime=" + timequery,
                  "timestep=1",
                  "parameters=Temperature,Pressure,Humidity,WindSpeedMS,"
                  "WindGust,MaximumWind,WeatherSymbol3"])

        latest_tstep = max(obs.data.keys())
        current_values = obs.data[latest_tstep][settings.LOCATION]

        self.__weatherdict = {
            "temperature": current_values["Air temperature"]['value'],
            "pressure": current_values['Air pressure']['value'],
            "humidity": current_values['Humidity']['value'],
            "windspeed": current_values['Wind speed']['value'],
            "windgust": current_values['Wind gust']['value'],
            "weathersymbol": int(current_values['Weather']['value'])
        }

        print(self.__weatherdict)

        return self.__weatherdict


def is_day(location):
    s = sun(location.observer, date=dt.date.today(), tzinfo=location.tzinfo)
    current_time = dt.datetime.now(tz=location.tzinfo)

    if s["sunrise"] < current_time < s["sunset"]:
        # print("Sun is up")
        return True
    else:
        # print("Sun is not up")
        return False
