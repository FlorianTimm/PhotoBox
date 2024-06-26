#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from typing import TYPE_CHECKING
from common.logger import Logger


Button = None
try:
    from gpiozero import Button  # type: ignore
except ImportError or NotImplementedError:
    Logger().warning("GPIO not available")
    Button = None

if TYPE_CHECKING:
    from master.control import Control


class ButtonControl:
    """
    A class that represents the control of buttons.

    Attributes:
        __control: The control object.

    Methods:
        __init__: Initializes the ButtonControl object.
        __red_button_held: Handles the event when the red button is held.
        __red_button_released: Handles the event when the red button is released.
        __blue_button_released: Handles the event when the blue button is released.
        __blue_button_held: Handles the event when the blue button is held.
        __green_button_released: Handles the event when the green button is released.
        __green_button_held: Handles the event when the green button is held.
    """

    def __init__(self, control: 'Control') -> None:
        """
        Initializes the ButtonControl object.

        Args:
            control: The control object.
        """
        self.__control = control

        if Button is not None:
            Logger().info("Buttons are starting...")
            self.__button_blue = Button(
                24, pull_up=True, hold_time=2, bounce_time=0.1)
            self.__button_blue.when_released = self.__blue_button_released
            self.__button_blue.when_held = self.__blue_button_held
            self.__button_blue_was_held = False

            self.__button_red = Button(
                23, pull_up=True, hold_time=2, bounce_time=0.1)
            self.__button_red.when_held = self.__red_button_held
            self.__button_red.when_released = self.__red_button_released
            self.__button_red_was_held = False

            self.__button_green = Button(
                25, pull_up=True, hold_time=2, bounce_time=0.1)
            self.__button_green.when_released = self.__green_button_released
            self.__button_green.when_held = self.__green_button_held
            self.__button_green_was_held = False

    # Buttons

    def __red_button_held(self, ) -> None:
        """
        Handles the event when the red button is held.
        """
        self.__button_red_was_held = True
        Logger().info("Shutdown pressed...")
        self.__control.system_control('shutdown')

    def __red_button_released(self, ) -> None:
        """
        Handles the event when the red button is released.
        """
        if not self.__button_red_was_held:
            Logger().info("Red pressed...")
            self.__control.switch_pause_resume()
            pass
        self.__button_red_was_held = False

    def __blue_button_released(self, ) -> None:
        """
        Handles the event when the blue button is released.
        """
        if not self.__button_blue_was_held:
            Logger().info("Photo pressed...")
            self.__control.capture_photo('photo')
        self.__button_blue_was_held = False

    def __blue_button_held(self, ) -> None:
        """
        Handles the event when the blue button is held.
        """
        self.__button_blue_was_held = True
        Logger().info("Stack pressed...")
        self.__control.capture_photo('stack')

    def __green_button_released(self, ) -> None:
        """
        Handles the event when the green button is released.
        """
        if not self.__button_green_was_held:
            Logger().info("Status LED pressed...")
            self.__control.get_leds().status_led(5)
        self.__button_green_was_held = False

    def __green_button_held(self, ):
        """
        Handles the event when the green button is held.
        """
        self.__button_green_was_held = True
        Logger().info("Search pressed...")
        self.__control.search_cameras()
