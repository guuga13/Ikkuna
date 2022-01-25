from astral import LocationInfo
import datetime

WIDTH_DISPLAY = 1920
HEIGHT_DISPLAY = 1080
MOVEMENT_SPEED = 1
FRAMERATE = 60
URL = "https://live-image.panomax.com/cams/4173/recent_full.jpg"
CAP_FEED_URL = 'https://alerts.fmi.fi/cap/feed/atom_fi-FI.xml'
LOCATION = "Kaukajärvi"
FULLSCREEN = True
locationinfo = LocationInfo('Tampere', 'Finland', 'Europe/Helsinki',
                            61.462528, 23.901936)
MANUAL_DATETIME = False
# MANUAL_DATETIME = datetime.datetime(year=2022, month=1, day=23, hour=21,
# tzinfo=locationinfo.tzinfo)
FONT_COLOR = "#d3cfca"
FONT_BG_COLOR = "#181a1b"

AREA = ["Pirkanmaa", "Tampere"]
GEOCODE = ["FI-11", "837"]
