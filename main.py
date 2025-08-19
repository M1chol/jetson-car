from concurrent.futures import ThreadPoolExecutor, wait
from steering import Steering
from time import sleep

with ThreadPoolExecutor() as executor:
    # Step one run setup in pararel

    print("[MAIN] Starting setup threads...")
    steering_future = executor.submit(Steering().setup)

    wait([steering_future])

    steering = steering_future.result()

    if steering:
        print("[MAIN] Setup threads finished successfully")
    else:
        print("[MAIN] Setup failed, quiting")
        quit()
    print("[MAIN] Starting workers...")

    steering.startWorker(executor)

    while not steering.getStatus():
        sleep(1)

    print("[MAIN] quit requested, closing threads")

    steering.stop()
