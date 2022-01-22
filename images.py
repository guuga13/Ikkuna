from tkinter import *
from PIL import Image, ImageTk
from io import BytesIO
import os

ws = Tk()
ws.title('PythonGuides')
ws.geometry('300x300')
ws.config(bg='#345')

frame = Frame(ws, bg="red")

names = ['pedestrianSafety.png', "trafficWeather.png", "coldWeather.png"]

labels = []
for image in names:
    symbolpath = os.path.normpath(os.path.join(os.getcwd(), 'lib',
                                               image))
    pil_image = Image.open(symbolpath)
    photo_image = ImageTk.PhotoImage(pil_image)
    label = Label(frame, image=photo_image)
    label.image = photo_image
    label.pack()
    labels.append(label)

frame.pack()

print(labels)

ws.mainloop()
