import arrow
from PIL import Image, ImageDraw
import qrcode
from pages import DisplayPage

class WiFi(DisplayPage):
    
    def __init__(self, dba, matrix, seconds=False):
        super().__init__(dba, matrix)
        if matrix is not None:
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'WiFi'
        self.qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=1,
                    border=4
                    )
        self.qrcode = Image.open("img/display.bmp")

    def update(self):
        self.nextUpdate = arrow.now().shift(hours=+1)
        
    def display(self):
        self.icon = Image.new("RGB", (128,64))
        self.icon.paste(self.qrcode, box=(0,0))
        if self.is_paused:
            draw = ImageDraw.Draw(self.icon)
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/thumb.bmp", "BMP")
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas

    def generate_qrcode(self,wifi_connect_string):
        self.qr.add_data(wifi_connect_string,optimize=20)
        self.qr.make(fit=True)
        qrcode = self.qr.make_image(fill_color="white", back_color="black")
        logo = Image.open("img/wifi-logo.bmp")
        icon = Image.new("RGB", (128,64))
        # draw = ImageDraw.Draw(icon)
        icon.paste(qrcode, box=(11,11))
        icon.paste(logo, box=(68,11))
        icon.save("img/display.bmp", "BMP")
        self.qrcode = icon
