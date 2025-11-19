from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from time import sleep

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32)

text = "Hello World"

with canvas(device) as draw:
    w, h = draw.textsize(text)  # default built-in font
    x = (device.width - w) // 2
    y = (device.height - h) // 2
    draw.text((x, y), text, fill=255)

sleep(20)