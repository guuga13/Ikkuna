import requests
import xmltodict
import json
import collections.abc

r = requests.get('https://alerts.fmi.fi/cap/feed/atom_fi-FI.xml')

dict_format = xmltodict.parse(r.content)
dict_format = dict_format["feed"]

for alert in dict_format["entry"]:
    for language in alert["content"]["alert"]["info"]:
        if isinstance(language["area"], collections.Mapping):
            if "polygon" in language["area"]:
                language["area"]["polygon"].clear()
        else:
            for area in language["area"]:
                area.pop('polygon', None)

with open('CAP_DATA_NONE_POLYGONS.json', 'w') as outfile:
    json.dump(dict_format, outfile)
