import configparser
import re
from time import sleep


gpio_available_ = False
try:
    import neopixel
    import board
    from gpiozero import Button
    from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
    gpio_available_ = True
except ImportError:
    print("GPIO not available")
    gpio_available_ = False
except NotImplementedError:
    print("GPIO not available")
    gpio_available_ = False


class LedControl:
    RED = (255, 75, 75)
    BLUE = (75, 75, 255)
    GREEN = (75, 255, 75)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 100)
    LIGHTRED = (50, 0, 0)

    white_light_on = False

    def __init__(self, conf: configparser.ConfigParser, control):
        self.gpio_available = gpio_available_
        self.conf = conf
        self.control = control

        if self.gpio_available:
            self.leds: list[int] = [int(v)
                                    for v in self.conf['server']['leds'].split(",")]
            pixel_pin: Pin = board.D18
            self.num_pixels: int = len(self.leds)

            self.pixels = neopixel.NeoPixel(
                pixel_pin, self.num_pixels, brightness=1, auto_write=True, pixel_order=neopixel.RGB)  # type: ignore

            self.starting()

    def switch_off(self):
        self.__fill(self.BLACK)

    def starting(self):
        self.__fill(self.BLUE)

    def waiting(self):
        self.__fill(self.YELLOW)

    def __fill(self, color):
        if not self.gpio_available:
            return
        self.pixels.fill(color)

    def status_led(self, val=0) -> None:
        if not self.gpio_available:
            return
        self.white_light_on = False

        for led, pi in enumerate(self.leds):
            self.pixels[led] = self.RED
            liste_aktuell = self.control.get_hostnames()
            for hostname, ip in liste_aktuell:
                n = re.findall(r"\d{2}", hostname)
                if len(n) > 0:
                    t = int(n[0])
                    if t == pi:
                        self.pixels[led] = self.GREEN
        if val > 0:
            sleep(float(val))
            self.photo_light()

    def photo_light(self, val=0) -> None:
        self.white_light_on = True
        self.__fill(self.WHITE)
        if (val > 0):
            sleep(float(val))
            self.status_led()

    def running_light(self):
        if not self.gpio_available:
            return
        self.switch_off()
        self.white_light_on = False
        while not self.control.get_cams_started():
            for j in range(self.num_pixels//8):
                for i in range(8):
                    self.pixels[j+self.num_pixels//8*i] = self.LIGHTRED
                sleep(0.5)
                for i in range(8):
                    self.pixels[j+self.num_pixels//8*i] = self.BLACK
                if self.control.get_cams_started():
                    break
