from concurrent.futures import ThreadPoolExecutor, wait
from car.steering import Steering
from car.fileHandler import FileHandler
from time import sleep
import json
from datetime import datetime
from pathlib import Path


def start(*, persistRun=False, debug=False):
    config = None

    # Create folder if data should be saved
    if persistRun:
        folder = makeDatedFolder("results")
    else:
        folder = Path("results/temp")

    with ThreadPoolExecutor() as executor:
        # Load config
        print("[CAR] Loading config file...")
        with open("car/config.json") as file:
            config = json.load(file)
            if not config:
                print("[CAR] Config file failed to load")
                quit()

        # Run setup in pararel
        print("[CAR] Starting setup threads...")
        file_handler_future = executor.submit(
            FileHandler(folder / "out.txt", debug=debug).setup
        )
        steering_future = executor.submit(
            Steering(config, debug).setup, file_handler_future
        )

        # steering setup already waits for servo and motor.
        wait([steering_future])

        steering = steering_future.result()
        file_handler = file_handler_future.result()

        if all([steering, file_handler]):
            print("[MAIN] Setup threads finished successfully")
        else:
            print("[MAIN] Setup failed, quiting")
            quit()
        print("[MAIN] Starting workers...")

        steering.startWorker(executor)
        file_handler.startWorker(executor)

        while not steering.getStatus():
            sleep(1)

        print("[MAIN] Steering requested quit, closing threads")

        steering.stop()
        file_handler.stop()

        while not all(
            [
                file_handler.getStatus(),
                steering.getStatus(),
            ]
        ):
            sleep(2)

        print("[MAIN] All threads closed successfully, adios")


def makeDatedFolder(base_path="."):
    folder_name = datetime.now().strftime("%Y-%m-%d")
    base = Path(base_path)
    target = base / folder_name

    counter = 1
    while target.exists():
        target = base / f"{folder_name}-{counter}"
        counter += 1

    target.mkdir(parents=True)
    return target

