#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from re import findall
from time import sleep
from typing import TYPE_CHECKING

from common.logger import Logger
from common.conf import Conf


if TYPE_CHECKING:
    from master.control import Control

NeoPixel = None
D18 = None
Pin = None
NeoPixelRGB = None
try:
    from neopixel import NeoPixel, RGB as NeoPixelRGB  # type: ignore
    from board import D18  # type: ignore
    from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin  # type: ignore
    led_available = True
except ImportError or NotImplementedError:
    Logger().warning("GPIO not available")
    NeoPixel = None
    D18 = None
    Pin = None
    NeoPixelRGB = None


class LedControl:
    """
    A class that controls the LEDs.

    Attributes:
        __RED (tuple): RGB values for red color.
        __BLUE (tuple): RGB values for blue color.
        __GREEN (tuple): RGB values for green color.
        __WHITE (tuple): RGB values for white color.
        __BLACK (tuple): RGB values for black color.
        __YELLOW (tuple): RGB values for yellow color.
        __LIGHTRED (tuple): RGB values for light red color.

    Methods:
        __init__(self, conf: configparser.Conf, control): Initializes the LedControl object.
        switch_off(self): Turns off all LEDs.
        starting(self): Sets the LEDs to blue color.
        waiting(self): Sets the LEDs to yellow color.
        __fill(self, color): Fills all LEDs with the specified color.
        status_led(self, val=0): Sets the LEDs based on the status of the control object.
        photo_light(self, val=0): Turns on white light and sets the LEDs to white color.
        running_light(self): Animates the LEDs with a running light effect.
    """

    __RED = (255, 75, 75)
    __BLUE = (75, 75, 255)
    __GREEN = (75, 255, 75)
    __WHITE = (255, 255, 255)
    __BLACK = (0, 0, 0)
    __YELLOW = (255, 255, 100)
    __LIGHTRED = (50, 0, 0)

    __photo_light_color = __WHITE

    def __init__(self, control: 'Control'):
        """
        Initializes the LedControl object.

        Args:
            control: The control object.

        Raises:
            None
        """
        global __gpio_available
        self.__conf = Conf().get()
        self.__control = control

        self.__pixels = None

        if D18 and NeoPixel and Pin:
            self.__leds: list[int] = [int(v)
                                      for v in self.__conf['server']['leds'].split(",")]
            pixel_pin = D18
            self.__num_pixels: int = len(self.__leds)

            self.__pixels = NeoPixel(
                pixel_pin, self.__num_pixels, brightness=1, auto_write=True, pixel_order=NeoPixelRGB)  # type: ignore

            self.starting()

    def switch_off(self):
        """
        Turns off all LEDs.

        Args:
            None

        Returns:
            None
        """
        self.__fill(self.__BLACK)

    def starting(self):
        """
        Sets the LEDs to blue color.

        Args:
            None

        Returns:
            None
        """
        self.__fill(self.__BLUE)

    def waiting(self):
        """
        Sets the LEDs to yellow color.

        Args:
            None

        Returns:
            None
        """
        self.__fill(self.__YELLOW)

    def __fill(self, color):
        """
        Fills all LEDs with the specified color.

        Args:
            color (tuple): RGB values for the color.

        Returns:
            None
        """
        if self.__pixels is None:
            return
        self.__pixels.fill(color)

    def status_led(self, val: float = 0) -> None:
        """
        Sets the LEDs based on the status of the control object.

        Args:
            val (float): The sleep duration in seconds.

        Returns:
            None
        """
        if self.__pixels is None:
            return

        for led, pi in enumerate(self.__leds):
            self.__pixels[led] = self.__RED
            liste_aktuell = self.__control.get_hostnames()
            for hostname in liste_aktuell:
                n = findall(r"\d{2}", hostname)
                if len(n) > 0:
                    t = int(n[0])
                    if t == pi:
                        self.__pixels[led] = self.__GREEN
        if val > 0:
            sleep(float(val))
            self.photo_light()

    def photo_light(self, val: float = 0) -> None:
        """
        Turns on white light and sets the LEDs to white color.

        Args:
            val (float): The sleep duration in seconds.

        Returns:
            None
        """
        self.__fill(self.__photo_light_color)
        if (val > 0):
            sleep(float(val))
            self.status_led()

    def running_light(self):
        """
        Animates the LEDs with a running light effect.

        Args:
            None

        Returns:
            None
        """
        if self.__pixels is None:
            return
        self.switch_off()
        while not self.__control.get_cams_started():
            for j in range(self.__num_pixels//8):
                for i in range(8):
                    self.__pixels[j+self.__num_pixels//8*i] = self.__LIGHTRED
                sleep(0.5)
                for i in range(8):
                    self.__pixels[j+self.__num_pixels//8*i] = self.__BLACK
                if self.__control.get_cams_started():
                    break

    def get_photo_light_color(self):
        return self.__photo_light_color

    def set_photo_light_color(self, color):
        self.__photo_light_color = color
        self.photo_light(5)
        return self.__photo_light_color
