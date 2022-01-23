import tkinter as tk
from pygame import mixer
root = tk.Tk()
deli = 100  # milliseconds of delay per character
svar = tk.StringVar()
labl = tk.Label(root, textvariable=svar, height=10)

mixer.init()

root.bind('b', lambda event: play_alarm())


def shif():
    shif.msg = shif.msg[1:] + shif.msg[0]
    svar.set(shif.msg)
    root.after(deli, shif)


def play_alarm():
    mixer.music.load("lib/ping.ogg")
    mixer.music.play()


shif.msg = ' Is this an alert, or what? '
shif.msg += "Tässä vähän lisää."
shif()
labl.pack()
root.mainloop()
