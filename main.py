from concurrent.futures import ThreadPoolExecutor, wait
from steering import Steering
from time import sleep
from fileHandler import FileHandler
import argparse

parser = argparse.ArgumentParser(description="Jetson powered autonomus car")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
args = parser.parse_args()

with ThreadPoolExecutor() as executor:
    # Step one run setup in pararel

    print("[MAIN] Starting setup threads...")
    motor_file_handler_future = executor.submit(FileHandler("motor.txt").setup)
    servo_file_handler_future = executor.submit(FileHandler("servo.txt").setup)
    steering_future = executor.submit(
        Steering(args.debug).setup, motor_file_handler_future, servo_file_handler_future
    )

    # steering setup already waits for servo and motor.
    wait([steering_future])

    steering = steering_future.result()
    motor_file_handler = motor_file_handler_future.result()
    servo_file_handler = servo_file_handler_future.result()

    if all([steering, motor_file_handler, servo_file_handler]):
        print("[MAIN] Setup threads finished successfully")
    else:
        print("[MAIN] Setup failed, quiting")
        quit()
    print("[MAIN] Starting workers...")

    steering.startWorker(executor)
    motor_file_handler.startWorker(executor)
    servo_file_handler.startWorker(executor)

    while not steering.getStatus():
        sleep(1)

    print("[MAIN] Steering requested quit, closing threads")

    steering.stop()
    motor_file_handler.stop()
    servo_file_handler.stop()

    while not all(
        [
            motor_file_handler.getStatus(),
            servo_file_handler.getStatus(),
            steering.getStatus(),
        ]
    ):
        sleep(2)

    print("[MAIN] All threads closed successfully, adios")
