import collections.abc
import json
import datetime as dt
AREA = ["Pirkanmaa", "Tampere"]
GEOCODE = ["FI-11", "837"]


# GET ALL ALERTS FOR TAMPERE (NOT CANCELS)
# CHECK ALL UPDATES AND CANCELS IF THEY REFERENCE PRIOR ALARM


def alert_for_current_area(alert):
    for area in alert["content"]['alert']['info'][0]['area']:
        if not isinstance(area, collections.Mapping):
            return False
        print(area)
        print(type(area))
        print(area["areaDesc"])
        if area["areaDesc"] in AREA:
            return True
        if area["geocode"]["value"] in GEOCODE:
            return True
    return False


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


with open("CAP_DATA_1.json") as json_file:
    CAP = json.load(json_file)
CAP = CAP["feed"]
alerts = {}

for alert in CAP["entry"]:
    # print(alert["title"])

    if alert_for_current_area(alert) and alert_msgtype(alert,
                                                       "Alert", "Update"):
        alerts[alert['id']] = \
            dict(title=alert['title'],
                 description=alert['content']['alert']['info'][0][
                     'description'],
                 color=alert["content"]["alert"]["info"][0]["parameter"][0][
                     "value"], expires=dt.datetime.fromisoformat(
                    alert["content"]["alert"]["info"][0]["expires"]))

for alert in CAP["entry"]:
    if alert_msgtype(alert, "Alert"):
        continue
    print(alert["content"]["alert"]["msgType"])
    references = alert["content"]["alert"]['references']
    references = references.split(' ')
    for i in range(len(references)):
        references[i] = references[i].split(',')[1]
        if references[i] in alerts:
            print("UPDATE FOUND")
            # delete alert
            alerts.pop(references[i])
    print(references)
    print(len(references))


    # WANTED PARAMETERS: Color, area, expires
print("FINAL")
for id, info in alerts.items():
    print(info["title"])
    print(info["expires"].tzinfo)
