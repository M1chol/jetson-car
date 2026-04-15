import json
from pathlib import Path
from time import sleep
from threading import Event

from concurrent.futures import ThreadPoolExecutor, wait

from car.fileHandler import FileHandler
from car.steering import Steering
from car.virtualGamepad import VirtualGamepad

steer = None
executor = None
motor_file_handler = None
car_stop_event = None
""" Setup and start car components @arg persistRun: bool - if data should be saved to dated folder"""
def start() -> VirtualGamepad:
    global steer, executor, motor_file_handler, car_stop_event
    with open("car/config.json") as file:
        config = json.load(file)
        if not config:
            print("Config file failed to load")
            quit()

    if executor is not None:
        stop()

    event = Event()
    car_stop_event = event
    gamepad = VirtualGamepad(
        carStopEvent=event,
        startCollectionEvent=event,
        config=config,
        debug=False,
    )

    executor = ThreadPoolExecutor()
    try:
        file_handler_future = executor.submit(
            FileHandler(Path("results/temp/out.txt"), startEvent=event).setup
        )
        steering_future = executor.submit(
            Steering(
                config,
                debug=False,
                startCollectionEvent=event,
                VIRTUAL_GAMEPAD=gamepad,
            ).setup,
            file_handler_future,
        )
        wait([steering_future])
        motor_file_handler = file_handler_future.result()
        steer = steering_future.result()
        if not steer:
            raise RuntimeError("steering init failed")

        if not all([steer, motor_file_handler]):
            raise RuntimeError("setup failed")

        print("[MAIN] Setup threads finished successfully")

        steer.startWorker(executor)
        motor_file_handler.startWorker(executor)
        return gamepad
    except Exception:
        stop()
        raise

def stop():
    global steer, executor, motor_file_handler, car_stop_event

    local_steer = steer
    local_executor = executor
    local_writer = motor_file_handler
    local_stop_event = car_stop_event

    steer = None
    executor = None
    motor_file_handler = None
    car_stop_event = None

    if local_stop_event:
        local_stop_event.set()

    if local_steer:
        local_steer.stop()

    if local_writer:
        local_writer.stop()

    deadline = 5.0
    started = 0.0
    while started < deadline:
        steering_stopped = local_steer is None or local_steer.getStatus()
        writer_stopped = local_writer is None or local_writer.getStatus()
        if steering_stopped and writer_stopped:
            break
        sleep(0.1)
        started += 0.1

    if local_executor:
        local_executor.shutdown(wait=True, cancel_futures=False)

    return True
