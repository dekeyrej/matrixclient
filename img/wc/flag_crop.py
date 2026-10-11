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

import json

from PIL import Image, UnidentifiedImageError
from urllib.request import urlopen

class WCFlags:
    def __init__(self):
        self.base_url = "https://a.espncdn.com/i/teamlogos/countries/500/"
    
    def grab_flag(self, country_code):
        url = f"{self.base_url}{country_code.lower()}.png"
        try:
            return Image.open(urlopen(url))
        except Exception as e:
            print(f"Error fetching flag for {country_code}: {e}")
            return None

    def crop_flag(self, flag_image):
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
            return None
        
if __name__ == "__main__":
    wc_flags = WCFlags()
    with open('wcgroups.json', 'r') as f:
        wcgroups = json.load(f)
        wccountries = [k for k in wcgroups.keys()]
        wccountries.sort()
    for country in wccountries:
        flag_image = wc_flags.grab_flag(country)
        if flag_image:
            cropped_flag = wc_flags.crop_flag(flag_image)
            if cropped_flag:
                with open(f"output/cropped/{country}.png", "wb") as f:
                    cropped_flag.save(f, format="PNG")
                scaled_flag = cropped_flag.resize((48, 32), Image.Resampling.LANCZOS)
                with open(f"output/scaled/{country}.bmp", "wb") as f:
                    scaled_flag.save(f, format="BMP")
    print("Done cropping and scaling flags for:", wccountries)