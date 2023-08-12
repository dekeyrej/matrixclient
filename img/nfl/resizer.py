from PIL import Image

conferences = ['AFC','NFC']
    
def createIcons():
    for c in conferences:
        image = Image.open(c + ".png")
#         image = image.crop((5,20,97,82))
        image = image.crop((32,100,468,400))
        image = image.resize((16,16),Image.Resampling.LANCZOS)
#         print(c)
#         image = image.resize((32,32),Image.Resampling.LANCZOS)
        image.convert('RGB')
        image.save(c + ".bmp", "BMP")
    
createIcons()

# image = Image.open("ARG.png")
# image = image.crop((5,20,97,82))
# image = image.resize((48,32),Image.Resampling.LANCZOS)
# image.convert('RGB')
# image.save("ARG-cropped-resized.bmp", "BMP")