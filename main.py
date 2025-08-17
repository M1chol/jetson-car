from concurrent.futures import ThreadPoolExecutor, wait
from steering import Steering

with ThreadPoolExecutor() as executor:
    # Step one run setup in pararel
    sterObj = Steering()
    sterObj.DEBUG = True

    print("[MAIN] Starting setup threads...")
    steering_future = executor.submit(sterObj.setup)

    wait([steering_future])

    steering = steering_future.result()

    if steering:
        print("[MAIN] Setup threads finished successfully")
    else:
        print("[MAIN] Setup failed, quiting")
        quit()
    print("[MAIN] Starting workers...")

    steering.startWorker(executor)

    # TODO: Add better system for tracking threads
    while input("type 'q' to quit: ") != "q":
        pass

    print("[MAIN] quit requested, closing threads")

    steering.stop()
