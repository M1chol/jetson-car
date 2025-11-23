from car.steering import Steering
from concurrent.futures import ThreadPoolExecutor, wait
from car.virtual_gamepad import VirtualGamepad
from car.fileHandler import FileHandler
from threading import Event
from time import sleep
import json

with open("config.json") as file:
    config = json.load(file)
    if not config:
        print("Config file failed to load")
        quit()

event = Event()
gamepad = VirtualGamepad(carStopEvent=event, config=config, debug=False)

with ThreadPoolExecutor as executor:
    
    motor_file_handler_future = executor.submit(FileHandler("motor.txt").setup)
    servo_file_handler_future = executor.submit(FileHandler("servo.txt").setup)
    steering_future = executor.submit(
        Steering(config, debug=False).setup, motor_file_handler_future, servo_file_handler_future
    )
    wait([steering_future])

    steer = steering_future.result()

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
