from car.steering import Steering
from concurrent.futures import ThreadPoolExecutor, wait
from car.virtualGamepad import VirtualGamepad
from car.fileHandler import FileHandler
from threading import Event
from time import sleep
from pathlib import Path
import json

with open("car/config.json") as file:
    config = json.load(file)
    if not config:
        print("Config file failed to load")
        quit()

event = Event()
gamepad = VirtualGamepad(carStopEvent=event,startCollectionEvent=event, config=config, debug=True)

with ThreadPoolExecutor() as executor:
    file_handler_future = executor.submit(FileHandler(Path("out.txt"), startEvent=event).setup)
    steering_future = executor.submit(
        Steering(config, debug=False,startCollectionEvent=event, VIRTUAL_GAMEPAD=gamepad).setup,
        file_handler_future,
    )
    wait([steering_future])
    motor_file_handler = file_handler_future.result()
    steer = steering_future.result()
    if not steer:
        print("steering init failed")
        raise Exception

    if all([steer, motor_file_handler]):
        print("[MAIN] Setup threads finished successfully")
    else:
        print("[MAIN] Setup failed, quiting")
        quit()

    steer.startWorker(executor)
    motor_file_handler.startWorker(executor)

    sleep(2)
    print("Speed 200")
    gamepad.currentSpeed = 200
    sleep(5)
    print("Speed 0")
    gamepad.currentSpeed = 0
    sleep(2)
    print("Angle 45")
    gamepad.currentAngle = 45
    sleep(2)
    print("Angle -45")
    gamepad.currentAngle = -45
    sleep(2)
    print("Angle 0")
    gamepad.currentAngle = 0
    sleep(2)
    print("Speed -200")
    gamepad.currentSpeed = -200
    sleep(5)
    print("Speed 0")
    gamepad.currentSpeed = 0
    print("Finish")
    sleep(2)
    steer.stop()
    motor_file_handler.stop()
