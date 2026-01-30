from car.steering import Steering
from concurrent.futures import ThreadPoolExecutor, wait
from car.virtualGamepad import VirtualGamepad
from car.fileHandler import FileHandler
from threading import Event
from time import sleep
from pathlib import Path
import json

with open("config.json") as file:
    config = json.load(file)
    if not config:
        print("Config file failed to load")
        quit()

event = Event()
gamepad = VirtualGamepad(carStopEvent=event,startCollectionEvent=event, config=config, debug=False)

with ThreadPoolExecutor() as executor:
    file_handler_future = executor.submit(FileHandler(Path("out.txt"), startEvent=event).setup)
    steering_future = executor.submit(
        Steering(config, debug=True, startCollectionEvent=event, VIRTUAL_GAMEPAD=gamepad).setup,
        file_handler_future
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

    print("Make sure hearbeat is not set")
    steer.STEER_MANUAL = True

    sleep(2)
    # Bypasing private method as it is a test code not meant to be run normally
    print("Front Right")
    steer.__setMotors([500, 0, 0, 0])
    sleep(5)
    print("Rear Right")
    steer.__setMotors([0, 500, 0, 0])
    sleep(5)
    print("Rear Left")
    steer.__setMotors([0, 0, 500, 0])
    sleep(5)
    print("Front Left")
    steer.__setMotors([0, 0, 0, 500])
    sleep(5)
    print("Finish")
    steer.stop()
    motor_file_handler.stop()
