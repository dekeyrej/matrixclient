import argparse

def parse_command_line_args():
    """
    Parse command line arguments for the microclient display application.
    
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    # Create the argument parser
    parser = argparse.ArgumentParser()
    # app arguments
    parser.add_argument("-i", "--init-rgb", action="store", help="Initialize an RGB Matrix Display. Default: 0 (no RGB display)", default=0, type=int)
    # rgbmatrix arguments   
    parser.add_argument("-r", "--led-rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32", default=32, type=int)
    parser.add_argument("--led-cols", action="store", help="Panel columns. Typically 32 or 64. (Default: 64)", default=64, type=int)
    parser.add_argument("-c", "--led-chain", action="store", help="Daisy-chained boards. Default: 4.", default=4, type=int)
    parser.add_argument("-P", "--led-parallel", action="store", help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1", default=1, type=int)
    parser.add_argument("-b", "--led-brightness", action="store", help="Sets brightness level. Default: 100. Range: 1..100", default=100, type=int)
    parser.add_argument("-m", "--led-gpio-mapping", help="Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm" , default='adafruit-hat', choices=['regular', 'regular-pi1', 'adafruit-hat', 'adafruit-hat-pwm'], type=str)
    parser.add_argument("--led-pixel-mapper", action="store", help="Apply pixel mappers. e.g \"Rotate:90\"", default="U-mapper", type=str)
    parser.add_argument("--led-show-refresh", action="store", help="Shows the current refresh rate of the LED panel")
    # parser.add_argument("--led-show-refresh", action="store_true", help="Shows the current refresh rate of the LED panel")
    parser.add_argument("--led-slowdown-gpio", action="store", help="Slow down writing to GPIO. Range: 0..4. Default: 4", default=4, type=int) # 2 works pretty well for a pi3A+, 4 for a pi4b
    parser.add_argument("--led-no-hardware-pulse", action="store", help="Don't use hardware pin-pulse generation")
    parser.add_argument("--led-rgb-sequence", action="store", help="Switch if your matrix has led colors swapped. Default: RGB", default="RGB", type=str)
    parser.add_argument("-p", "--led-pwm-bits", action="store", help="Bits used for PWM. Something between 1..11. Default: 11", default=11, type=int)
    parser.add_argument("--led-pwm-lsb-nanoseconds", action="store", help="Base time-unit for the on-time in the lowest significant bit in nanoseconds. Default: 130", default=130, type=int)
    parser.add_argument("--led-scan-mode", action="store", help="Progressive or interlaced scan. 0 Progressive, 1 Interlaced (default)", default=1, choices=range(2), type=int)        
    # mlb arguments
    parser.add_argument("-t", action="store", help="2/3 letter abbreviation for the MLB team to display. BOS, TB, NYY. Befault: BOS", default="BOS", type=str)
    parser.add_argument("--enable-cycle", action="store_true", help="Enable cycling through all daily games when selected team's game is not in progress")
    return parser.parse_args()