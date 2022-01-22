import time
import datetime as dt
from tkinter import *
import requests
from PIL import Image, ImageTk
from io import BytesIO
import os
from astral import LocationInfo
from astral.sun import sun
import json
import collections.abc
from fmiopendata.wfs import download_stored_query

WIDTH_DISPLAY = 1920
HEIGHT_DISPLAY = 1080
MOVEMENT_SPEED = 1
URL = "https://live-image.panomax.com/cams/4173/recent_full.jpg"
LOCATION = "Kaukajärvi"
Image.MAX_IMAGE_PIXELS = 150000000

locationinfo = LocationInfo('Tampere', 'Finland', 'Europe/Helsinki',
                            61.462528, 23.901936)
MANUAL_DATETIME = dt.datetime(year=2022, month=1, day=16, hour=21,
                              tzinfo=locationinfo.tzinfo)

FONT_COLOR = "#d3cfca"
FONT_BG_COLOR = "#181a1b"

AREA = ["Pirkanmaa", "Tampere"]
GEOCODE = ["FI-11", "837"]


# URL = "https://www.thelabradorsite.com/wp-content/uploads/2019/03/Black-Lab-Your-Guide-To-The-Black-Labrador-Retriever-LS-long-1.jpg"

class WeatherInfo:
    def __init__(self, GUI):
        self.GUI = GUI

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
            args=["place=" + LOCATION,
                  "starttime=" + timequery,
                  "endtime=" + timequery,
                  "timestep=1",
                  "parameters=Temperature,Pressure,Humidity,WindSpeedMS,"
                  "WindGust,MaximumWind,WeatherSymbol3"])

        latest_tstep = max(obs.data.keys())
        current_values = obs.data[latest_tstep][LOCATION]

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
    # tampere = LocationInfo('Tampere', 'Finland', 'Europe/Helsinki',
    #  61.462528, 23.901936)
    s = sun(location.observer, date=dt.date.today(), tzinfo=location.tzinfo)

    current_time = dt.datetime.now(tz=location.tzinfo)

    if s["sunrise"] < current_time < s["sunset"]:
        # print("Sun is up")
        return True
    else:
        # print("Sun is not up")
        return False


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


def process_alerts(CAP_feed):
    alerts = {}
    for alert in CAP_feed["entry"]:
        # print(alert["title"])
        # Add alerts and updates to dict
        if alert_for_current_area(alert) and alert_msgtype(alert,
                                                           "Alert", "Update"):
            color = ""
            for parameter in alert["content"]["alert"]["info"][0]["parameter"]:
                if parameter['valueName'] == 'color':
                    color = parameter['value']
                    break

            alerts[alert['id']] = \
                dict(title=alert['title'],
                     description=alert['content']['alert']['info'][0][
                         'description'],
                     color=color, expires=dt.datetime.fromisoformat(
                        alert["content"]["alert"]["info"][0]["expires"]),
                     onset=dt.datetime.fromisoformat(
                         alert["content"]["alert"]["info"][0]["onset"]),
                     eventCode=
                     alert["content"]["alert"]["info"][0]['eventCode']['value']
                     )

    for alert in CAP_feed["entry"]:
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


def get_warnings_PLACEHOLDER():
    with open("CAP_DATA_1.json") as json_file:
        CAP = json.load(json_file)
    return CAP["feed"]


class Panorama:
    def __init__(self, parent, image):
        self.__parent = parent
        self.__canvas = parent.bg_canvas
        self.__running = True
        print(f"Panorame Class {self} INIT")
        image.thumbnail((image.size[0], HEIGHT_DISPLAY))
        self.__origPhoto = image
        print(self.__origPhoto.size)

        if image.size[0] > 1920:
            print("WIDE IMAGE, panning...")
            self.pan()
        else:
            print("showing static image")
            photoimage = ImageTk.PhotoImage(image)
            self.__canvas.itemconfigure(self.__parent.bg_canvas_picture,
                                        image=photoimage)
            self.__canvas.image = photoimage

    def __del__(self):
        print(f"Panorama {self} deleted")

    def pan(self, left_border=0):
        if not self.__running:
            return
        # print(f"panning, x={left_border}")
        length = self.__origPhoto.size[1]
        width = self.__origPhoto.size[0]
        x = self.__origPhoto
        if left_border >= width:
            left_border = 0
            print("täysi kierros")
        # self.debugwrite(left_border)

        right_border = WIDTH_DISPLAY + left_border

        if right_border >= width:
            print("next photo needed")
            # print(f"leftB={left_border}rightB={right_border}")
            self.__origPhoto.crop()
            next_photo = self.__origPhoto.crop((0, 0,
                                                (right_border - width),
                                                length))
            # print(f"Next photo right border {right_border - width}")
            old_photo = self.__origPhoto.crop((left_border, 0,
                                               width, length))
            # print(f"Old photo left border={left_border}, right border {
            # width}") print(f"old photo width={old_photo.size[0]}")
            current_frame = Image.new('RGB', (WIDTH_DISPLAY, HEIGHT_DISPLAY))
            current_frame.paste(old_photo, (0, 0))
            current_frame.paste(next_photo, (old_photo.width, 0))
            photoimage = ImageTk.PhotoImage(current_frame)

            self.__canvas.itemconfigure(self.__parent.bg_canvas_picture,
                                        image=photoimage)
            self.__canvas.image = photoimage
            new_left_border = left_border + MOVEMENT_SPEED
            # print(f"new left border= {new_left_border}")
            self.__parent.after(16, self.pan, new_left_border)
            return

        current_frame = self.__origPhoto.crop((left_border, 0,
                                               right_border, length))
        # print(f"current frame section ({left_border},{right_border})")
        photoimage = ImageTk.PhotoImage(current_frame)
        # self.bg_canvas_picture.configure(image=photoimage)
        # self.bg_canvas_picture.image = photoimage
        self.__canvas.itemconfigure(self.__parent.bg_canvas_picture,
                                    image=photoimage)
        self.__canvas.image = photoimage
        new_left_border = left_border + MOVEMENT_SPEED

        self.__parent.mainwindow.after(16, self.pan, new_left_border)

    def disable(self):
        self.__running = False


class GUI:
    def __init__(self):
        self.mainwindow = Tk()
        self.mainwindow.attributes('-fullscreen', True)

        self.bg_canvas = Canvas(self.mainwindow, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_canvas_picture = \
            self.bg_canvas.create_image(WIDTH_DISPLAY / 2,
                                        HEIGHT_DISPLAY / 2,
                                        anchor='center')

        self.__debugField = Label(self.mainwindow, width=10, height=2,
                                  text="debug")
        self.__debugField.pack()

        self.__clockRunning = True
        self.__current_panorama = None

        self.__location = LocationInfo('Tampere', 'Finland', 'Europe/Helsinki',
                                       61.462528, 23.901936)

        self.testbutton = Button(self.mainwindow, text="GET",
                                 command=self.downloader)
        self.testbutton.pack()

        self.__exitbutton = Button(text="Exit", width=13, height=3, bg="red",
                                   font=("Arial", 25), command=self.exit)
        self.__exitbutton.pack(side=BOTTOM)

        self.__warning_symbols_frame = Frame(self.bg_canvas, bg="red")
        self.__warning_symbols_frame.place(x=WIDTH_DISPLAY * (5 / 12),
                                           y=HEIGHT_DISPLAY * (8 / 10))

        self.mainwindow.bind('q', lambda event: self.exit())
        self.mainwindow.bind('d', lambda event: self.downloader())

        self.alerts = {}
        self.current_warning_symbols = []

        # image1 = Image.open(
        #     r"C:\Users\Pyry Nieminen\Pictures\S7\20180517_050556.jpg")
        # image1 = image1.rotate(270, expand=1)
        # self.drawimage(image1)
        self.__debugField.pack_forget()
        self.testbutton.pack_forget()
        self.__exitbutton.pack_forget()
        self.downloader()
        self.create_clock()
        self.init_weather()
        # self.get_warnings()

        self.mainwindow.mainloop()

    def remove_expired_alerts(self):
        current_time = dt.datetime.now(tz=self.__location.tzinfo)
        if MANUAL_DATETIME:
            current_time = MANUAL_DATETIME

        for id in list(self.alerts.keys()):
            if self.alerts[id]["expires"] < current_time:
                print(f"EXPIRED ALARM REMOVED - {self.alerts[id]['title']} EXP"
                      f" - {self.alerts[id]['expires']}")
                del self.alerts[id]

    def get_warnings(self):
        cap_feed = get_warnings_PLACEHOLDER()
        self.alerts = process_alerts(cap_feed)
        self.draw_warnings()

    def draw_an_alert(self, alert_id, priority):
        if priority == "info":
            # Draw infobox
            print(
                f"Drawing a {priority} priority alarm."f" onset= {self.alerts[alert_id]['onset']} expires= {self.alerts[alert_id]['expires']} color={self.alerts[alert_id]['color']}")
            print(self.alerts[alert_id]['title'])

        elif priority == "yellow":
            # Draw a warning symbol corresponding warning symbol
            print(
                f"Drawing a {priority} priority alarm."f" onset= {self.alerts[alert_id]['onset']} expires= {self.alerts[alert_id]['expires']} color={self.alerts[alert_id]['color']}")
            print(self.alerts[alert_id]['title'])
            # Create photoimage
            event_code = self.alerts[alert_id]["eventCode"]
            symbolpath = os.path.normpath(os.path.join(os.getcwd(), 'lib',
                                                       f'{event_code}.png'))
            wsymbol = Image.open(symbolpath)
            photoimagewsymbol = ImageTk.PhotoImage(wsymbol)
            warning_label = Label(self.bg_canvas,
                                  image=photoimagewsymbol)
            # Create label with correct tag
            warning_label.place(x=WIDTH_DISPLAY / 2, y=HEIGHT_DISPLAY / 2)


        elif priority == "orange":
            # Draw an orange ticker on top of the screen

            print(
                f"Drawing a {priority} priority alarm."f" onset= {self.alerts[alert_id]['onset']} expires= {self.alerts[alert_id]['expires']} color={self.alerts[id]['color']}")
            print(self.alerts[alert_id]['title'])
        elif priority == "red":
            # Draw a red ticker and sound an alarm

            print(
                f"Drawing a {priority} priority alarm."f" onset= {self.alerts[alert_id]['onset']} expires= {self.alerts[alert_id]['expires']} color={self.alerts[alert_id]['color']}")
            print(self.alerts[alert_id]['title'])
        else:
            raise ValueError(
                f"'{priority}' is not an allowed priority value")

    def draw_warnings(self):
        self.remove_expired_alerts()
        current_time = dt.datetime.now(tz=self.__location.tzinfo)
        if MANUAL_DATETIME:
            current_time = MANUAL_DATETIME
        for id, info in self.alerts.items():
            if info["color"] == "red":
                # Red warning
                self.draw_an_alert(id, info["color"])
            elif info["onset"] < current_time:
                # Warning is currenty in force
                self.draw_an_alert(id, info["color"])
            elif info["onset"] < (current_time + dt.timedelta(days=1)) \
                    and info["color"] == "orange":
                # An orange warning for tomorrow
                self.draw_an_alert(id, "info")

        # TODO remove not current alarms
        self.current_warning_symbols.clear()

        self.mainwindow.after(1000 * 60, self.draw_weather)

    def init_weather(self):
        param = {"font": ("Dubai Medium", "50"),
                 "fill": FONT_COLOR,
                 "anchor": "sw"}

        weather_bar = {
            "numbers": self.bg_canvas.create_text(WIDTH_DISPLAY * (1 / 6),
                                                  HEIGHT_DISPLAY * (9 / 10),
                                                  param),
            "small numbers": self.bg_canvas.create_text(
                WIDTH_DISPLAY * (1 / 6),
                HEIGHT_DISPLAY * (18.5 / 20), param,
                font=("Dubai Medium", "30"),
                text="904 hPa 89% 1 m/s"),
            "weathersymbol": self.bg_canvas.create_image(
                WIDTH_DISPLAY * (1 / 6),
                HEIGHT_DISPLAY * (9.25 / 10),
                anchor=SE)
        }

        cwd = os.getcwd()
        print(cwd)
        images = os.path.normpath(os.path.join(cwd, 'lib', '1.png'))
        print(images)
        image1 = Image.open(images)
        image1 = image1.reduce(2)
        photoimagesunny = ImageTk.PhotoImage(image1)

        self.bg_canvas.itemconfigure(weather_bar["weathersymbol"],
                                     image=photoimagesunny)
        self.bg_canvas.weatherimage = photoimagesunny

        self.get_weather(weather_bar)

    def get_weather(self, weather_bar):
        weatherdownloader = WeatherInfo(self)
        self.draw_weather(weather_bar, weatherdownloader)
        self.mainwindow.after(1000 * 60, self.get_weather, weather_bar)

    def draw_weather(self, weatherbar, weatherdownloader):
        weatherdict = weatherdownloader.get_weather()
        upper_text = f"{round(weatherdict['temperature'])}°C" \
                     f" {round(weatherdict['windspeed'])} m/s"
        lower_text = f"{round(weatherdict['pressure'])} hPa" \
                     f" {round(weatherdict['humidity'])}% " \
                     f"{round(weatherdict['windgust'])} m/s"

        self.bg_canvas.itemconfigure(weatherbar["numbers"],
                                     text=upper_text)
        self.bg_canvas.itemconfigure(weatherbar["small numbers"],
                                     text=lower_text)
        # Weathersymbol

        bbox = self.bg_canvas.bbox(weatherbar["numbers"],
                                   weatherbar["small numbers"],
                                   weatherbar["weathersymbol"])

        rect_item = self.bg_canvas.create_rectangle(bbox, fill=FONT_BG_COLOR,
                                                    outline=FONT_BG_COLOR)
        self.bg_canvas.tag_raise(weatherbar["numbers"], rect_item)
        self.bg_canvas.tag_raise(weatherbar["small numbers"], rect_item)
        self.bg_canvas.tag_raise(weatherbar["weathersymbol"], rect_item)

        print(f"{weatherdict['weathersymbol']}")
        if not is_day(self.__location):
            symbolpath = os.path.normpath(os.path.join(os.getcwd(), 'lib',
                                                       f'{weatherdict["weathersymbol"]}N.png'))
            try:
                wsymbol = Image.open(symbolpath)
            except FileNotFoundError:
                symbolpath = os.path.normpath(os.path.join(os.getcwd(), 'lib',
                                                           f'{weatherdict["weathersymbol"]}.png'))
                wsymbol = Image.open(symbolpath)


        else:
            symbolpath = os.path.normpath(os.path.join(os.getcwd(), 'lib',
                                                       f'{weatherdict["weathersymbol"]}.png'))
            wsymbol = Image.open(symbolpath)

        wsymbol = wsymbol.reduce(2)
        photoimagewsymbol = ImageTk.PhotoImage(wsymbol)

        self.bg_canvas.itemconfigure(weatherbar["weathersymbol"],
                                     image=photoimagewsymbol)
        self.bg_canvas.weatherimage = photoimagewsymbol

    def create_clock(self):
        clock = self.bg_canvas.create_text(WIDTH_DISPLAY * (5 / 6),
                                           HEIGHT_DISPLAY * (9 / 10),
                                           anchor='se',
                                           font=(
                                               "Dubai Medium", "50",),
                                           fill=FONT_COLOR
                                           )
        bbox = self.bg_canvas.bbox(clock)
        rect_item = self.bg_canvas.create_rectangle(bbox, outline=FONT_BG_COLOR
                                                    , fill=FONT_BG_COLOR)
        self.bg_canvas.tag_raise(clock, rect_item)
        self.update_clock(clock)

    def downloader(self, num_of_tries=0):
        print(f"downloader() num={num_of_tries}")
        download_success = self.get_image()
        if download_success:
            print("download succesfull")
            self.mainwindow.after(600000, self.downloader)
            return

        print("download error, retrying")
        num_of_tries += 1
        if num_of_tries < 4:
            print("rapid retry")
            self.mainwindow.after(2000, self.downloader, num_of_tries)
        elif num_of_tries < 10:
            print("slow retry")
            # 1000 * 60 * 1
            self.mainwindow.after(1000 * 60 * 1, self.downloader,
                                  num_of_tries)
        else:
            print("download error")
            self.debugwrite("download error.")

    def get_image(self):
        try:
            responce = requests.get(URL, timeout=1)
        except requests.exceptions.RequestException as e:
            return False

        print(responce.status_code)

        print(responce.headers['Content-Type'])

        if responce.status_code == 200 and responce.headers[
            'Content-Type'] == "image/jpeg":
            image = Image.open(BytesIO(responce.content))
            print(f"IMAGE TYPE IS -> {type(image)}")

            # file = open("sample_image.jpeg", "wb")
            # file.write(responce.content)
            # file.close()

            self.drawimage(image)
            return True
        else:
            print("IMAGE DOWNLOAD FAILURE")
            return False

    def debugwrite(self, data):
        self.__debugField.configure(text=data)

    def drawimage(self, image):
        print("drawimage()")
        if self.__current_panorama is not None:
            print("DELETING PREVIOUS CLASS")
            print(type(self.__current_panorama))
            print(self.__current_panorama)
            self.__current_panorama.disable()
        self.__current_panorama = Panorama(self, image)


    def CAP(self, etag=False):
        print("CAP!!!")
        print(f"current etag={etag}")

        r = requests.head('https://alerts.fmi.fi/cap/feed/atom_fi-FI.xml')
        new_etag = r.headers['Etag']
        print(f"new etag={etag}")
        print(f"{etag}=={new_etag}")
        if etag == new_etag:
            print("sama etag -- Ei haeta uudestaan")
        else:
            print("eri etag. Haetaan uudestaan")
            # TODO tallenna etag

        self.mainwindow.after(1000 * 20, self.CAP, etag)

    def update_clock(self, clock):

        now = time.strftime("%H:%M")
        self.bg_canvas.itemconfigure(clock, text=now)
        bbox = self.bg_canvas.bbox(clock)
        rect_item = self.bg_canvas.create_rectangle(bbox,
                                                    fill=FONT_BG_COLOR)
        self.bg_canvas.tag_raise(clock, rect_item)
        self.mainwindow.after(1000, self.update_clock, clock)
        return

    def exit(self):
        self.mainwindow.destroy()


def main():
    GUI()


main()
