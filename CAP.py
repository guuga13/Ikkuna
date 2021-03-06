import collections.abc
import json
import datetime as dt

import requests
import xmltodict

from settings import AREA, GEOCODE, locationinfo, MANUAL_DATETIME
import settings


class FmiAlert:
    def __init__(self, init_dict):
        self.alert_id = init_dict["alert_id"]
        self.title = init_dict["title"]
        self.description = init_dict["description"]
        self.color = init_dict["color"]

        self.expires = init_dict["expires"]
        self.onset = init_dict["onset"]
        self.eventCode = init_dict["eventCode"]

    def expired(self):
        current_time = dt.datetime.now(tz=locationinfo.tzinfo)
        if MANUAL_DATETIME:
            current_time = MANUAL_DATETIME
        if self.expires < current_time:
            return True
        else:
            return False

    def in_effect(self, hours=0):
        current_time = dt.datetime.now(tz=locationinfo.tzinfo)
        if MANUAL_DATETIME:
            current_time = MANUAL_DATETIME
        if hours == 0:
            if self.onset < current_time and not self.expired():
                # warning currently in force
                return True
            else:
                return False
        else:
            if not self.in_effect() and self.onset < current_time + dt. \
                    timedelta(hours=hours):
                # Warning not inforce but will be inforce in the next PARAM
                # hours
                return True
            else:
                return False

    def __repr__(self):
        return self.title


def alert_msgtype(alert_msg, *alert_types):
    allowed_types = ["Alert", "Update", "Cancel"]
    alert_type = alert_msg["content"]["alert"]["msgType"]

    for wanted_type in alert_types:
        if wanted_type not in allowed_types:
            raise ValueError(
                f"'{wanted_type}' is not an allowed alert msgType.")
        if alert_type == wanted_type:
            return True

    return False


def process_alerts(cap_feed):
    alerts = {}
    for alert in cap_feed["entry"]:
        # print(alert["title"])
        # Add alerts and updates to list
        if alert_for_current_area(alert) and alert_msgtype(alert,
                                                           "Alert", "Update"):
            color = ""
            for parameter in alert["content"]["alert"]["info"][0]["parameter"]:
                if parameter['valueName'] == 'color':
                    color = parameter['value']
                    break

            init_dict = dict(
                alert_id=alert['id'],
                title=alert['title'],
                description=
                alert['content']['alert']['info'][0][
                    'description'],
                color=color,
                expires=dt.datetime.fromisoformat(
                    alert["content"]["alert"]["info"][0][
                        "expires"]),
                onset=dt.datetime.fromisoformat(
                    alert["content"]["alert"]["info"][0][
                        "onset"]),
                eventCode=
                alert["content"]["alert"]["info"][0][
                    'eventCode']['value']
            )
            alerts[alert['id']] = FmiAlert(init_dict)

    for alert in cap_feed["entry"]:
        # Check every update and cancel
        if alert_msgtype(alert, "Alert"):
            continue
        # print(alert["content"]["alert"]["msgType"])
        # If update or cancel references existing alert, that alert is deleted
        references = alert["content"]["alert"]['references']
        references = references.split(' ')
        for i in range(len(references)):
            references[i] = references[i].split(',')[1]
            if references[i] in alerts:
                print("UPDATE FOUND")
                # delete alert
                alerts.pop(references[i])
    return alerts


def download_cap_PLACEHOLDER():
    with open("CAP_DATA_NONE_POLYGONS.json") as json_file:
        CAP = json.load(json_file)
    return CAP


def alert_for_current_area(alert):
    for area in alert["content"]['alert']['info'][0]['area']:
        if not isinstance(area, collections.abc.Mapping):
            return False
        # print(area)
        # print(type(area))
        # print(area["areaDesc"])
        if area["areaDesc"] in AREA:
            return True
        if area["geocode"]["value"] in GEOCODE:
            return True
    return False


def get_warnings(etag=None):
    print(f"get_warnings() etag={etag}")
    if not etag:
        print("trying to open from filesystem")
        try:
            with open("weather_warnings_fmi.json", encoding='utf-8') as f:
                warning_json = json.load(f)
                print("success")
                success = True
        except OSError:  # parent of IOError, OSError *and* WindowsError where
            # available
            print("Cant open warning json file")
            success = False

        if success:
            file_etag = warning_json.get("etag")
            result = warnings_download(file_etag)
            if result:
                return result
            else:
                return warning_json

        else:
            return warnings_download()
    else:
        return warnings_download(etag)


def warnings_download(prev_etag=None):
    print(f"warnings_download() prev_etag={prev_etag}")
    try:
        print("gettind header")
        head = requests.head(settings.CAP_FEED_URL)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    new_etag = head.headers["etag"]
    print(f"new_etag = {new_etag}")
    if new_etag == prev_etag:
        print(f"{new_etag} == {prev_etag}, returning false")
        # same etag as previous
        print()
        return False
    print(f"{new_etag} != {prev_etag}, -> GET()")
    try:
        r = requests.get(settings.CAP_FEED_URL)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    print("xmltodic")
    dict_format = xmltodict.parse(r.content)
    dict_format = dict_format["feed"]
    dict_format["etag"] = new_etag
    print("deleting polygons")

    for alert in dict_format["entry"]:
        for language in alert["content"]["alert"]["info"]:
            if isinstance(language["area"], collections.Mapping):
                if "polygon" in language["area"]:
                    if isinstance(language["area"]["polygon"], str):
                        language["area"].pop("polygon", None)
                    else:
                        language["area"]["polygon"].clear()
            else:
                for area in language["area"]:
                    area.pop('polygon', None)

    print("saving to file")
    with open('weather_warnings_fmi.json', 'w') as outfile:
        json.dump(dict_format, outfile)
    print("returning dict_format")
    return dict_format


def remove_expired_alerts(alert_dict):
    for alert_id in list(alert_dict):
        if alert_dict[alert_id].expired():
            print(
                f"EXPIRED ALARM REMOVED - {alert_dict[alert_id]['title']} EXP"
                f" - {alert_dict[alert_id]['expires']}")
            del alert_dict[alert_id]

    return alert_dict
