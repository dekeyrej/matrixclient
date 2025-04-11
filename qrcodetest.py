from PIL import Image, ImageDraw
import qrcode
wifi_connect_string = "WIFI:S:eightchr;T:WPA;P:somerandopileofcharsoftherightlengthtooq;;"

qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=4
        )
qr.add_data(wifi_connect_string,optimize=20)
qr.make(fit=True)
qrc = qr.make_image(fill_color="white", back_color="black")
qrc = qrc.convert("RGB")
# qrc.save("wifi_qr.bmp", "BMP")
# print(qrc.size)
logo = Image.open("img/wifi-logo.bmp")
# print(logo.size)
icon = Image.new("RGB", (128,64))
icon.paste(qrc, box=(11,11))
icon.paste(logo, box=(61,11))
icon.save("wifi.bmp", "BMP")