from concurrent.futures import ThreadPoolExecutor, wait, Future
from typing import Any
from car.steering import Steering
from time import sleep
import json
from pathlib import Path
import shutil
from threading import Event
from car.virtualGamepad import VirtualGamepad

steering = None
pool = None
""" Setup and start car components @arg persistRun: bool - if data should be saved to dated folder"""
def start(pad: VirtualGamepad, debug=False) -> bool:
    global steering, pool
    # Load config
    print("[SETUP] Loading config file...")
    with open("car/config.json") as file:
        config = json.load(file)
        if not config:
            print("[SETUP] Config file failed to load")
            return False

    folder = Path("results/temp")
    frames_folder = folder / "frames"

    if frames_folder.exists():
        shutil.rmtree(frames_folder)
    frames_folder.mkdir(parents=True, exist_ok=True)

    pool = ThreadPoolExecutor()
    steering_future = pool.submit(Steering(config, debug=debug, startCollectionEvent=Event(), VIRTUAL_GAMEPAD=pad).setup)
    print("[SETUP] Starting setup threads...")
    futures: list[Future[Any]] = [steering_future]
    wait(futures)
    steering = steering_future.result()
    if not steering or not steering.fileWriter:
        print("[SETUP] Steering setup failed")
        return False

    print("[SETUP] Setup threads finished successfully")
    print("[SETUP] Starting workers...")

    steering.startWorker(pool)
    return True

def stop():
    print("[SETUP] Steering requested quit, closing threads")

    steering.stop()
    
    while not steering.getStatus():
        sleep(1)
    pool.shutdown()
    print("[SETUP] All threads closed successfully, adios")
    return True

