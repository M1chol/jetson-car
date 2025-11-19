from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageDraw, Image
import socket
from time import sleep
import os

serial = i2c(port=7, address=0x3C)
device = ssd1306(serial, width=128, height=32)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = None
    finally:
        s.close()
    return ip


with canvas(device) as draw:
    draw.text(
        (device.width // 2, device.height // 2),
        "Waiting for network...",
        fill=255,
        anchor="mm",
    )

    ip = None
    while not ip:
        ip = get_local_ip()
        sleep(0.5)


img = Image.new("1", device.size)
draw = ImageDraw.Draw(img)
draw.text((device.width // 2, device.height // 2), ip, fill=255, anchor="mm")
device.display(img)

os._exit(0)
