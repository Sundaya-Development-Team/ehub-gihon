import time
import sys
import board
import signal
import neopixel

from datetime import datetime, timedelta
from gpiozero import Button

from utils import send_command
from config import redis_instance as red

BUTTON_PIN = 24

btn = Button(BUTTON_PIN, bounce_time=0.05, hold_time=1.5, pull_up=False)

timer = 0

pixel_pin = board.D18
num_pixels = 1

ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

def get_status_can():
    output = send_command("ifconfig can0")
    return True if output.find('UP') > 0 else False

def get_status_rs():
    status = int(red.get('error') if int(red.get('error')) is not None else False)
    return status

def get_status_ehub():
    output = send_command("sudo systemctl is-failed handle_canbus.service")
    return True if output.rstrip() == 'active' else False

def get_status_lan():
    output = send_command("ifconfig eth0")
    return True if output.find('UP') > 0 else False

def blink(col):
    options = {
        'red':(255,0,0),
        'green': (0,255,0),
        'blue': (0,0,255)
    }
    pixels.fill(options[col])
    pixels.show()
    time.sleep(0.25)

    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(0.25)

def check_status():
    btn.when_released = None
    btn.when_held = None
    print('button pressed : check status')
    blink('green') if get_status_ehub() else blink('red')
    blink('green') if get_status_can() else blink('red')
    blink('green') if get_status_rs() else blink('red')
    blink('green') if get_status_lan() else blink('red')
    btn.when_released = check_status
    btn.when_held = wifi_handler

def wifi_handler():
    print('button hold : wifi handler')
    btn.when_released = None
    btn.when_held = None
    wifi_status = send_command('sudo systemctl is-failed hostapd.service').rstrip()
    if wifi_status == 'active':
        send_command('sudo systemctl stop hostapd.service')
        send_command('sudo systemctl disable hostapd.service')
        pixels.fill((0, 0, 0))
        pixels.show()
        btn.when_released = check_status
        btn.when_held = wifi_handler
    else:
        send_command('sudo systemctl enable hostapd.service')
        send_command('sudo systemctl restart hostapd.service')
        blink('blue')
        pixels.fill((0, 0, 175))
        pixels.show()
        btn.when_held = wifi_handler

def signal_handler(sig, frame):
    pixels.fill((0, 0, 0))
    pixels.show()
    sys.exit(0)

if __name__ == "__main__":
    pixels.fill((0, 0, 0))
    pixels.show()
    btn.when_released = check_status
    btn.when_held = wifi_handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()

