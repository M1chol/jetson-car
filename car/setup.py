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
from car.virtualFileHandler import VirtualFileWriter

""" Setup and start car components @arg persistRun: bool - if data should be saved to dated folder"""
def start(*, persistRun=False, debug=False) -> bool:
    
    # Load config
    print("[SETUP] Loading config file...")
    with open("car/config.json") as file:
        config = json.load(file)
        if not config:
            print("[SETUP] Config file failed to load")
            return False

    load_camera = config["CAMERA"]["ENABLED"]
    if load_camera:
        print("[SETUP] Will try to run camera setup")

    # Create folder if data should be saved
    if persistRun:
        folder = makeDatedFolder("results")
    else:
        folder = Path("results/temp")
    frames_folder = folder / "frames"

    if frames_folder.exists():
        shutil.rmtree(frames_folder)
    frames_folder.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        # Run setup in pararel
        print("[SETUP] Starting setup threads...")
        file_handler_future = executor.submit(
            FileHandler(folder / "out.txt", debug=debug).setup
        )
        steering_future = executor.submit(
            Steering(config, debug).setup, file_handler_future
        )
        if load_camera:
            camera_file_handler_future = executor.submit(
                FileHandler(folder / "camera_timings.txt", debug=debug).setup
            )
            camera_future = executor.submit(
                Camera(config, frames_folder, debug=debug).setup, camera_file_handler_future
            )
        else:
            camera_future = executor.submit(
                VirtualCamera().setup, VirtualFileWriter()
            )

        # steering setup already waits for servo and motor.
        futures: list[Future[Any]] = [steering_future, camera_future]
        wait(futures)

        steering = steering_future.result()
        camera = camera_future.result()
        if not steering.fileWriter:
            print("[SETUP] Steering fileHandler setup failed")
            return False
        if not camera.fileWriter:
            print("[SETUP] Camera fileHandler setup failed")
            return False
        steering_file_handler = steering.fileWriter.result()
        camera_file_handler = camera.fileWriter.result()
        if not camera:
            print("[SETUP] Camera setup failed")
            return False
        if not steering:
            print("[SETUP] Steering setup failed")
            return False
        if not steering_file_handler:
            print("[SETUP] Steering FileHandler setup failed")
            return False
        if not camera_file_handler:
            print("[SETUP] Camera FileHandler setup failed")
            return False

        print("[SETUP] Setup threads finished successfully")
        print("[SETUP] Starting workers...")

        steering.startWorker(executor)
        steering_file_handler.startWorker(executor)
        camera.startWorker(executor)
        camera_file_handler.startWorker(executor)

        while not steering.getStatus():
            sleep(1)

        print("[SETUP] Steering requested quit, closing threads")

        steering.stop()
        steering_file_handler.stop()
        camera.stop()
        camera_file_handler.stop()

        while not all(
            [
                steering.getStatus(),
                steering_file_handler.getStatus(),
                camera.getStatus(),
                camera_file_handler.getStatus(),
            ]
        ):
            sleep(1)

        print("[SETUP] All threads closed successfully, adios")
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

