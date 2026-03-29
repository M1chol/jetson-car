from concurrent.futures import ThreadPoolExecutor, wait, Future
from typing import Any
from car.steering import Steering
from time import sleep
import json
from pathlib import Path
import shutil
from threading import Event
from car.virtualGamepad import VirtualGamepad
from car.fileHandler import FileHandler

steer = None
executor = None
""" Setup and start car components @arg persistRun: bool - if data should be saved to dated folder"""
def start(debug=False) -> VirtualGamepad:
    global steer, executor 
    with open("car/config.json") as file:
        config = json.load(file)
        if not config:
            print("Config file failed to load")
            quit()

    event = Event()
    gamepad = VirtualGamepad(carStopEvent=event,startCollectionEvent=event, config=config, debug=False)

    executor = ThreadPoolExecutor()
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
    return gamepad

def stop():
    global steer, executor
    print("[SETUP] Steering requested quit, closing threads")
    if steer:
        steer.stop()
    
    while not steer.getStatus():
        sleep(1)
    executor.shutdown()
    print("[SETUP] All threads closed successfully, adios")
    return True

