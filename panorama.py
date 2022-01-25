from PIL import Image, ImageTk
import requests
from settings import HEIGHT_DISPLAY, WIDTH_DISPLAY, MOVEMENT_SPEED, URL
from io import BytesIO


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
        if left_border >= width:
            left_border = 0
            print("täysi kierros")
        # self.debugwrite(left_border)

        right_border = WIDTH_DISPLAY + left_border

        if right_border >= width:
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
            self.__parent.mainwindow.after(16, self.pan, new_left_border)
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


def downloader(root, num_of_tries=0):
    print(f"downloader() num={num_of_tries}")
    download_success = get_image(root)
    if download_success:
        print("download succesfull")
        root.mainwindow.after(600000, downloader, root)
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
        print(f"IMAGE TYPE IS -> {type(image)}")

        # file = open("sample_image.jpeg", "wb")
        # file.write(responce.content)
        # file.close()

        root.drawimage(image)
        return True
    else:
        print("IMAGE DOWNLOAD FAILURE")
        return False
