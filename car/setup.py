from concurrent.futures import ThreadPoolExecutor, wait, Future
from typing import Any
from car.steering import Steering
from car.fileHandler import FileHandler
from car.camera import Camera
from car.virtualCamera import VirtualCamera
from time import sleep
import json
from datetime import datetime
from pathlib import Path
import shutil

""" Setup and start car components @arg persistRun: bool - if data should be saved to dated folder"""
def start(*, persistRun=False, debug=False) -> bool:
    
    # Load config
    print("[CAR] Loading config file...")
    with open("car/config.json") as file:
        config = json.load(file)
        if not config:
            print("[CAR] Config file failed to load")
            return False

    load_camera = config["CAMERA"]["ENABLED"]

    # Create folder if data should be saved
    if persistRun:
        folder = makeDatedFolder("results")
    else:
        folder = Path("results/temp")
    frames_folder = folder / "frames"

    if frames_folder.exists():
        shutil.rmtree(frames_folder)
    else:
        frames_folder.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        # Run setup in pararel
        print("[CAR] Starting setup threads...")
        file_handler_future = executor.submit(
            FileHandler(folder / "out.txt", debug=debug).setup
        )
        steering_future = executor.submit(
            Steering(config, debug).setup, file_handler_future
        )
        if load_camera:
            camera_future = executor.submit(
                Camera(config, frames_folder, debug=debug).setup
            )
        else:
            camera_future = executor.submit(
                VirtualCamera().setup
            )

        # steering setup already waits for servo and motor.
        futures: list[Future[Any]] = [steering_future, camera_future]
        wait(futures)

        steering = steering_future.result()
        file_handler = file_handler_future.result()
        camera = camera_future.result()
        if not camera:
            print("[MAIN] Camera setup failed")
            return False
        if not steering:
            print("[MAIN] Steering setup failed")
            return False
        if not file_handler:
            print("[MAIN] FileHandler setup failed")
            return False

        if all([steering, file_handler]):
            print("[MAIN] Setup threads finished successfully")
        else:
            print("[MAIN] Setup failed, quiting")
            quit()
        print("[MAIN] Starting workers...")

        steering.startWorker(executor)
        file_handler.startWorker(executor)
        camera.startWorker(executor)

        while not steering.getStatus():
            sleep(1)

        print("[MAIN] Steering requested quit, closing threads")

        steering.stop()
        file_handler.stop()
        camera.stop()

        while not all(
            [
                file_handler.getStatus(),
                steering.getStatus(),
                camera.getStatus(),
            ]
        ):
            sleep(2)

        print("[MAIN] All threads closed successfully, adios")
        return True


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

