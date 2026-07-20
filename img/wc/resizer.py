"""
Image.crop(left, upper, right, lower)

(0,0)  Left
  +-----|-------------------------+

  |     |                         |
  |     |                         |
Upper --+-------------------+     |

  |     |                   |     |
  |     |   CROPPED AREA    |     |
  |     |                   |     |
  |     +-------------------+-- Lower

  |                         |     |
  |                         |     |
  +-------------------------|-----+
                          Right   (Width, Height)
"""

from PIL import Image, UnidentifiedImageError
from urllib.request import urlopen

countries = [
   'ALG', 'ARG', 'AUS', 'AUT', 'BEL', 'BIH', 'BRA', 'CAN', 
   'CIV', 'COD', 'COL', 'CPV', 'CRO', 'CUW', 'CZE', 'ECU', 
   'EGY', 'ENG', 'ESP', 'FRA', 'GER', 'GHA', 'HAI', 'IRN', 
   'IRQ', 'JOR', 'JPN', 'KOR', 'KSA', 'MAR', 'MEX', 'NED', 
   'NOR', 'NZL', 'PAN', 'PAR', 'POR', 'QAT', 'RSA', 'SCO', 
   'SEN', 'SUI', 'SWE', 'TUN', 'TUR', 'URU', 'USA', 'UZB']

def grab_flag(country_code):
   url = f"https://a.espncdn.com/i/teamlogos/countries/500/{country_code.lower()}.png"
   try:
      return Image.open(urlopen(url))
   except Exception as e:
      print(f"Error fetching flag for {country_code}: {e}")
      raise e

def crop_flag(flag_image):
   try:
      width, height = flag_image.size
      left = 19
      top = 96
      right = width -20
      bottom = height - 95
      cropped_image = flag_image.crop((left, top, right, bottom))
      return cropped_image
   except UnidentifiedImageError as e:
      print(f"Error processing flag image: {e}")
      raise e

def resize_flag(cropped_image, width=48, height=32):
   try:
       image = cropped_image.resize((width, height),Image.Resampling.LANCZOS)
       image.convert('RGB')
       return image
   except Exception as e:
       print(f"Error creating icon for {country_code}: {e}")
       raise e

def save_flag(scaled_flag, country_code):
   try:
       with open(f"{country_code}.bmp", "wb") as f:
                    scaled_flag.save(f, format="BMP")
   except Exception as e:
       print(f"Error saving icon for {country_code}: {e}")
       raise e

def createIcons():
   for c in countries:
      try:
         image = grab_flag(c)
         image = crop_flag(image)
         image = resize_flag(image, 48, 32)
         save_flag(image, c)
      except Exception as e:
         print(f"Error processing flag for {c}: {e}")

if __name__ == "__main__":
   createIcons()
