import requests
import xmltodict
import json

r = requests.get('https://alerts.fmi.fi/cap/feed/atom_fi-FI.xml')

dict_format = xmltodict.parse(r.content)

with open('CAP_DATA_1.json', 'w') as outfile:
    json.dump(dict_format, outfile)
