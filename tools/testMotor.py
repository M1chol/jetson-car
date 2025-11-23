from car.steering import Steering
from concurrent.futures import ThreadPoolExecutor
from car.virtual_gamepad import VirtualGamepad
from time import sleep
import json

with open("config.json") as file:
    config = json.load(file)
    if not config:
        print("Config file failed to load")
        quit()


gamepad = VirtualGamepad(config=config, debug=False)

steer = Steering(config=config, debug=False, VIRTUAL_GAMEPAD=gamepad)
steer.setup()

with ThreadPoolExecutor as executor:
    steer.startWorker(executor)

    sleep(2)
    gamepad.currentGas = 200
    sleep(2)
    gamepad.currentGas = 0
    sleep(2)
    gamepad.currentAngle = 45
    sleep(2)
    gamepad.currentAngle = -45
    sleep(2)
    gamepad.currentAngle = 0
    sleep(2)
    gamepad.currentBreak = 200
    sleep(2)
    gamepad.currentBreak = 0