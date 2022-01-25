from PIL import Image, ImageTk
import requests
from settings import HEIGHT_DISPLAY, WIDTH_DISPLAY, MOVEMENT_SPEED, URL, \
    FRAMERATE
from io import BytesIO


class Panorama:
    def __init__(self, parent, image):
        self.__parent = parent
        self.__canvas = parent.bg_canvas
        self.__running = True
        self.__image_obj = self.__parent.bg_canvas_picture
        self.__frametime = round(1000 / FRAMERATE)
        # print(f"Panorame Class {self} INIT")
        image.thumbnail((image.width, HEIGHT_DISPLAY))
        self.__origPhoto = image

        if image.size[0] > 1920:
            print("WIDE IMAGE, panning...")
            self.__currPhoto = self.expand(self.__origPhoto)
            # print(self.__origPhoto.size)
            photoimage = ImageTk.PhotoImage(self.__currPhoto)
            self.__canvas.itemconfigure(self.__image_obj,
                                        image=photoimage)
            self.__canvas.image = photoimage
            self.move()
        else:
            print("showing static image")
            photoimage = ImageTk.PhotoImage(self.__origPhoto)
            self.__canvas.itemconfigure(self.__image_obj,
                                        image=photoimage)
            self.__canvas.image = photoimage

    def __del__(self):
        print(f"Panorama {self} deleted")

    @staticmethod
    def expand(image):
        addition = image.crop((image.width - WIDTH_DISPLAY, 0,
                               image.width, HEIGHT_DISPLAY))
        # print(f"Old photo left border={image.width - WIDTH_DISPLAY},"
        # f" right bordr{image.width}")

        new_image = Image.new('RGB', (image.width + addition.width,
                                      HEIGHT_DISPLAY))
        new_image.paste(addition, (0, 0))
        new_image.paste(image, (addition.width, 0))
        # print(
        # f"NEW PHOTO {new_image.size[0]}x{new_image.size[1]} !!!")

        return new_image

    def move(self, x=0):
        if not self.__running:
            return
        left = x
        right = x + WIDTH_DISPLAY
        # print(f"move() {left}-{right}")
        # print(f"imagesize {self.__currPhoto.size}")
        width = self.__currPhoto.width

        if right >= width:
            #
            self.__canvas.move(self.__image_obj, width - WIDTH_DISPLAY, 0)
            self.__parent.mainwindow.after(self.__frametime, self.move)
            return
        self.__canvas.move(self.__image_obj, -MOVEMENT_SPEED, 0)
        new_left = MOVEMENT_SPEED + left
        self.__parent.mainwindow.after(self.__frametime, self.move, new_left)

    def disable(self):
        self.__running = False


def downloader(root, num_of_tries=0):
    print(f"downloader() num={num_of_tries}")
    download_success = get_image(root)
    if download_success:
        print("download succesfull")
        root.mainwindow.after(10 * 60 * 1000, downloader, root)
        return

    print("download error, retrying")
    num_of_tries += 1
    if num_of_tries < 4:
        print("rapid retry")
        root.mainwindow.after(2000, downloader, root, num_of_tries)
    elif num_of_tries < 10:
        print("slow retry")
        # 1000 * 60 * 1
        root.mainwindow.after(1000 * 60 * 1, downloader, root,
                              num_of_tries)
    else:
        print("download error")
        root.debugwrite("download error.")


def get_image(root):
    try:
        responce = requests.get(URL, timeout=1)
    except requests.exceptions.RequestException as e:
        return False

    print(responce.status_code)

    print(responce.headers['Content-Type'])

    if responce.status_code == 200 and responce.headers['Content-Type'] \
            == "image/jpeg":
        image = Image.open(BytesIO(responce.content))

        # file = open("sample_image.jpeg", "wb")
        # file.write(responce.content)
        # file.close()

        root.drawimage(image)
        return True
    else:
        print("IMAGE DOWNLOAD FAILURE")
        return False
