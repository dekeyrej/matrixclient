import arrow
from PIL import Image, ImageDraw
import qrcode
from rgbleddisplay import RGBLEDDisplay
import logging

class WiFi(RGBLEDDisplay):

    def __init__(self, matrix, connect_str):
        super().__init__(matrix=matrix)
        if matrix is not None:
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'WiFi'
        self.qrcode = self.generate_qrcode(connect_str)

    def update(self):
        self.nextUpdate = arrow.now().shift(hours=+1)
        
    def display(self):
        if self.data_dirty:
            self.icon = Image.new("RGB", (128,64))
            self.icon.paste(self.qrcode, box=(0,0))
            if self.is_paused:
                draw = ImageDraw.Draw(self.icon)
                draw.line(((125,0),(125,2)), fill='White', width=1)
                draw.line(((127,0),(127,2)), fill='White', width=1)
            self.icon.save("static/wifi.bmp", "BMP")
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas

    def generate_qrcode(self,wifi_connect_string):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=1,
            border=4
            )
        qr.add_data(wifi_connect_string,optimize=20)
        qr.make(fit=True)
        qrc = qr.make_image(fill_color="white", back_color="black")
        qrc = qrc.convert("RGB")  # required change based on the qrcode or PIL library version
        logo = Image.open("img/wifi-logo.bmp")
        icon = Image.new("RGB", (128,64))
        icon.paste(qrc, box=(11,11))
        icon.paste(logo, box=(61,11))
        return icon
