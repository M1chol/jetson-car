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

with ThreadPoolExecutor() as executor:
    motor_file_handler_future = executor.submit(FileHandler("motor.txt").setup)
    servo_file_handler_future = executor.submit(FileHandler("servo.txt").setup)
    steering_future = executor.submit(
        Steering(config, debug=False, VIRTUAL_GAMEPAD=gamepad).setup,
        motor_file_handler_future,
        servo_file_handler_future,
    )
    wait([steering_future])
    motor_file_handler = motor_file_handler_future.result()
    servo_file_handler = servo_file_handler_future.result()
    steer = steering_future.result()

    if all([steer, motor_file_handler, servo_file_handler]):
        print("[MAIN] Setup threads finished successfully")
    else:
        print("[MAIN] Setup failed, quiting")
        quit()

    steer.startWorker(executor)
    motor_file_handler.startWorker(executor)
    servo_file_handler.startWorker(executor)
    
    steer.STEER_MANUAL = True

    steer.__setMotors(500, 0, 0, 0)
    sleep(5)
    steer.__setMotors(0, 500, 0, 0)
    sleep(5)
    steer.__setMotors(0, 0, 500, 0)
    sleep(5)
    steer.__setMotors(0, 0, 0, 500)
    
    sleep(5)
    print("Finish")
    steer.stop()
    motor_file_handler.stop()
    servo_file_handler.stop()
