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


class ButtonControl:
    def __init__(self, control) -> None:
        self.gpio_available = gpio_available_
        self.control = control

        if self.gpio_available:
            print("Buttons are starting...")
            self.button_blue = Button(
                24, pull_up=True, hold_time=2, bounce_time=0.1)
            self.button_blue.when_released = self.blue_button_released
            self.button_blue.when_held = self.blue_button_held
            self.button_blue_was_held = False

            self.button_red = Button(
                23, pull_up=True, hold_time=2, bounce_time=0.1)
            self.button_red.when_held = self.red_button_held
            self.button_red.when_released = self.red_button_released
            self.button_red_was_held = False

            self.button_green = Button(
                25, pull_up=True, hold_time=2, bounce_time=0.1)
            self.button_green.when_released = self.green_button_released
            self.button_green.when_held = self.green_button_held
            self.button_green_was_held = False

  # Buttons

    def red_button_held(self, ) -> None:
        self.button_red_was_held = True
        print("Shutdown pressed...")
        self.control.system_control('shutdown')

    def red_button_released(self, ) -> None:
        if not self.button_red_was_held:
            print("Red pressed...")
            self.control.switch_pause_resume()
            pass
        self.button_red_was_held = False

    def blue_button_released(self, ) -> None:
        if not self.button_blue_was_held:
            print("Photo pressed...")
            self.control.capture('photo')
        self.button_blue_was_held = False

    def blue_button_held(self, ) -> None:
        self.button_blue_was_held = True
        print("Stack pressed...")
        self.control.capture('stack')

    def green_button_released(self, ) -> None:

        if not self.button_green_was_held:
            print("Status LED pressed...")
            self.control.get_leds().status_led(5)
        self.button_green_was_held = False

    def green_button_held(self, ):
        self.button_green_was_held = True
        print("Search pressed...")
        self.control.search()
