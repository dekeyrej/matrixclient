import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))
from rgbmatrix import RGBMatrix, RGBMatrixOptions

def init_matrix(clargs):
        # Configuration for the matrix
        options = RGBMatrixOptions()
        options.rows = clargs.led_rows
        options.cols = clargs.led_cols
        options.chain_length = clargs.led_chain
        options.parallel = clargs.led_parallel
        options.brightness = clargs.led_brightness
        options.hardware_mapping = clargs.led_gpio_mapping  # If you have an Adafruit HAT: 'adafruit-hat'
        options.pixel_mapper_config = clargs.led_pixel_mapper # "U-mapper;Rotate:180"
        if clargs.led_show_refresh is not None:
            options.show_refresh_rate = True
        if clargs.led_slowdown_gpio != None:
            options.gpio_slowdown = clargs.led_slowdown_gpio
        if clargs.led_no_hardware_pulse:
            options.disable_hardware_pulsing = True
    #         options.disable_hardware_pulsing = True   # force = True for running inside Thonny (don't have to run as root)
        options.led_rgb_sequence = clargs.led_rgb_sequence
        options.pwm_bits = clargs.led_pwm_bits
        options.pwm_lsb_nanoseconds = clargs.led_pwm_lsb_nanoseconds
        options.scan_mode = clargs.led_scan_mode

        return RGBMatrix(options = options)