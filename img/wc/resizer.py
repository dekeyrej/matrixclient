from PIL import Image

countries = ['ARG','AUS','BEL','BRA','CAN','CMR','CRC','CRO',
             'DEN','ECU','ENG','ESP','FRA','GER','GHA','IRN',
             'JPN','KOR','KSA','MAR','MEX','NED','POL','POR',
             'QAT','SEN','SRB','SUI','TUN','URU','USA','WAL']
    
def createIcons():
    for c in countries:
        image = Image.open(c + ".png")
        image = image.crop((5,20,97,82))
        image = image.resize((48,32),Image.Resampling.LANCZOS)
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