import datetime as dt
import os
import time
from tkinter import *

import requests
from PIL import Image, ImageTk
from pygame import mixer
import CAP
import panorama
from settings import *
from weather import WeatherInfo, is_day

Image.MAX_IMAGE_PIXELS = 150000000


class Ticker(Frame):
    def __init__(self, parent, priority):
        Frame.__init__(self, parent)
        self.parent = parent
        self.__string_var = StringVar()
        self.priority = priority
        self.label = Label(parent, textvariable=self.__string_var,
                           height=3, width=WIDTH_DISPLAY,
                           font=("Arial", 25))
        if self.priority == "high":
            self.label.configure(bg="orange", height=3)
        else:
            self.label.configure(bg="#D9D2CD", height=1)
        self.__string_var.set("TEST")
        self.__active = False

    def activate(self, message):
        self.__active = True
        if self.priority == "high":
            self.label.pack()
        else:
            self.label.pack(side=BOTTOM)
        self.shift(message)

    def shift(self, msg):
        if not self.__active:
            return
        msg = msg[1:] + msg[0]
        self.__string_var.set(msg)
        self.parent.after(100, self.shift, msg)

    def delete(self):
        self.label.pack_forget()
        self.__active = False


class TickerManager(Frame):
    def __init__(self, parent, priority):
        self.priority = priority
        self.parent = parent
        Frame.__init__(self, parent)
        self.parent = parent

        self.__current_ticker = Ticker(self.parent, priority)
        self.__message = ""
        self.parent = parent
        self.__alerts = []
        self.__active = False

    def append(self, alert):
        print(f"append() {alert}")
        if alert in self.__alerts:
            print(f"Already exits!")
            return
        self.check_for_expired()
        self.add_text(alert)
        self.__alerts.append(alert)
        self.show()

    def add_text(self, alert):
        print(f"add_text() {alert}")
        new_text = f" —— {alert.title} – {alert.description}"
        if self.__alerts:
            self.__message += f" —— ——  {new_text}"
        else:
            self.__message += new_text
        if alert.color == "red":
            self.__current_ticker.label.configure(bg="red")

    def check_for_expired(self, cont=False):
        print(f"check_for_expired()")
        redraw = False
        for alert in self.__alerts:
            if alert.expired():
                self.__alerts.pop(alert)
                redraw = True
        if redraw:
            self.__current_ticker.delete()
            self.__current_ticker = Ticker(self.parent, self.priority)
            self.__current_ticker.label.configure(bg="orange")
            if self.__alerts:
                for alert in self.__alerts:
                    self.add_text(alert)
                self.__current_ticker.activate(self.__message)
            else:
                self.hide()
        if not cont:
            return
        else:
            self.parent.after(1 * 60 * 1000, self.check_for_expired, True)

    def show(self):

        self.__current_ticker.activate(self.__message)

    def hide(self):

        self.__current_ticker.delete()
        self.__current_ticker = Ticker(self.parent, self.priority)


def play_alarm():
    mixer.music.load("lib/ping.ogg")
    mixer.music.play()


class GUI:
    def __init__(self):
        self.mainwindow = Tk()
        self.mainwindow.attributes('-fullscreen', FULLSCREEN)

        self.bg_canvas = Canvas(self.mainwindow, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_canvas_picture = \
            self.bg_canvas.create_image(0,
                                        0,
                                        anchor='nw')

        self.__debugField = Label(self.mainwindow, width=10, height=2,
                                  text="debug")
        self.__debugField.pack()

        self.__clockRunning = True
        self.__current_panorama = None

        self.__exitbutton = Button(text="Exit", width=13, height=3, bg="red",
                                   font=("Arial", 25), command=self.exit)
        self.__exitbutton.pack(side=BOTTOM)

        self.__warning_symbols_frame = Frame(self.bg_canvas, bg="#f6d402")
        self.__warning_symbols_frame.place(x=WIDTH_DISPLAY * (8 / 20),
                                           y=HEIGHT_DISPLAY * (8 / 10))
        self.__alert_ticker = TickerManager(self.mainwindow, "high")
        self.__info_ticker = TickerManager(self.mainwindow, "info")
        self.mainwindow.bind('q', lambda event: self.exit())
        self.mainwindow.bind('d', lambda event: panorama.downloader(self))
        self.mainwindow.bind('b', lambda event: self.draw_warnings())
        self.alerts = {}
        self.current_warning_symbols = []
        self.__etag = None
        # image1 = Image.open(
        #     r"C:\Users\Pyry Nieminen\Pictures\S7\20180517_050556.jpg")
        # image1 = image1.rotate(270, expand=1)
        # self.drawimage(image1)
        self.__debugField.pack_forget()

        self.__exitbutton.pack_forget()
        mixer.init()

        panorama.downloader(self)
        self.create_clock()
        self.init_weather()
        self.get_warnings()

        self.mainwindow.mainloop()

    def get_warnings(self):
        cap_feed = CAP.get_warnings(self.__etag)
        if cap_feed:
            # New update
            self.alerts = CAP.process_alerts(cap_feed)
            self.draw_warnings()
        self.mainwindow.after(5 * 60 * 1000, self.get_warnings)

    def draw_an_alert(self, alert, priority):
        if priority == "info":
            # Draw infobox
            print(f"Drawing a {priority} priority .onset= {alert.onset}"
                  f" expires= {alert.expires} color={alert.color}")
            print(alert)
            self.__info_ticker.append(alert)

        elif priority == "yellow":
            # Draw a warning symbol corresponding warning symbol
            print(f"Drawing a {priority} priority .onset= {alert.onset}"
                  f" expires= {alert.expires} color={alert.color}")
            print(alert)
            # Create photoimage
            imagepath = os.path.join(os.getcwd(), 'lib',
                                     f'{alert.eventCode}.png')
            symbolpath = os.path.normpath(imagepath)
            wsymbol = Image.open(symbolpath)
            photoimagewsymbol = ImageTk.PhotoImage(wsymbol)
            warning_label = Label(self.__warning_symbols_frame,
                                  image=photoimagewsymbol, bg="#f6d402")
            warning_label.image = photoimagewsymbol

            warning_label.pack(side=RIGHT)
            self.current_warning_symbols.append(warning_label)

        elif priority == "orange":
            print(f"Drawing a {priority} priority .onset= {alert.onset}"
                  f" expires= {alert.expires} color={alert.color}")
            print(alert)
            # Draw an orange ticker on top of the screen
            self.__alert_ticker.append(alert)

        elif priority == "red":
            # Draw a red ticker and sound an alarm
            print(f"Drawing a {priority} priority .onset= {alert.onset}"
                  f" expires= {alert.expires} color={alert.color}")
            print(alert)
            self.__alert_ticker.append(alert)
            play_alarm()
        else:
            raise ValueError(
                f"'{priority}' is not an allowed priority value")

    def draw_warnings(self):
        self.alerts = CAP.remove_expired_alerts(self.alerts)

        for alert_image in self.current_warning_symbols:
            # delete current alert images
            alert_image.destroy()

        current_time = dt.datetime.now(tz=locationinfo.tzinfo)
        if MANUAL_DATETIME:
            current_time = MANUAL_DATETIME
        for alert_id, alert in self.alerts.items():
            if alert.color == "red":
                # Red warning
                self.draw_an_alert(alert, alert.color)
            elif alert.in_effect():
                # Warning is currenty in force
                self.draw_an_alert(alert, alert.color)
            elif alert.in_effect(hours=24) and alert.color == "orange":
                # An orange warning for tomorrow
                self.draw_an_alert(alert, "info")
        self.mainwindow.after(1 * 60 * 1000, self.draw_warnings)

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
        images = os.path.normpath(os.path.join(cwd, 'lib', '1.png'))
        image1 = Image.open(images)
        image1 = image1.reduce(2)
        photoimagesunny = ImageTk.PhotoImage(image1)

        self.bg_canvas.itemconfigure(weather_bar["weathersymbol"],
                                     image=photoimagesunny)
        self.bg_canvas.weatherimage = photoimagesunny

        self.get_weather(weather_bar)

    def get_weather(self, weather_bar):
        weatherdownloader = WeatherInfo()
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

        self.__warning_symbols_frame.place(x=bbox[2], y=bbox[3], anchor=SW)

        if not is_day(locationinfo):
            imag_path = (os.path.join(os.getcwd(), 'lib',
                                      f'{weatherdict["weathersymbol"]}N.png'))
            symbolpath = os.path.normpath(imag_path)
            try:
                wsymbol = Image.open(symbolpath)
            except FileNotFoundError:
                imag_path = os.path.join(os.getcwd(), 'lib',
                                         f'{weatherdict["weathersymbol"]}.png')
                symbolpath = os.path.normpath(imag_path)
                wsymbol = Image.open(symbolpath)


        else:
            imag_path = os.path.join(os.getcwd(), 'lib',
                                     f'{weatherdict["weathersymbol"]}.png')
            symbolpath = os.path.normpath(imag_path)
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

    def debugwrite(self, data):
        self.__debugField.configure(text=data)

    def drawimage(self, image):
        # print("drawimage()")
        if self.__current_panorama is not None:
            # print("DELETING PREVIOUS CLASS")
            # print(type(self.__current_panorama))
            # print(self.__current_panorama)
            self.__current_panorama.disable()
        self.__current_panorama = panorama.Panorama(self, image)

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
        print("EXITING")
        self.mainwindow.destroy()
