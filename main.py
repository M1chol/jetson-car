from concurrent.futures import ThreadPoolExecutor, wait
from steering import Steering
from time import sleep
from fileHandler import FileHandler

with ThreadPoolExecutor() as executor:
    # Step one run setup in pararel

    print("[MAIN] Starting setup threads...")
    steering_file_handler_future = executor.submit(FileHandler("result.txt").setup)
    steering_future = executor.submit(Steering().setup, steering_file_handler_future)

    wait([steering_future, steering_file_handler_future])

    steering = steering_future.result()
    steering_file_handler = steering_file_handler_future.result()

    if all([steering, steering_file_handler]):
        print("[MAIN] Setup threads finished successfully")
    else:
        print("[MAIN] Setup failed, quiting")
        quit()
    print("[MAIN] Starting workers...")

    steering.startWorker(executor)
    steering_file_handler.startWorker(executor)

    while not steering.getStatus():
        sleep(1)

    print("[MAIN] Steering requested quit, closing threads")

    steering.stop()
    steering_file_handler.stop()

    while not all([steering_file_handler.getStatus(), steering.getStatus()]):
        sleep(1)

    print("[MAIN] All threads closed successfully, adios")
