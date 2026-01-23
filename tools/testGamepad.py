from car.steering import Steering
import json

with open("config.json") as file:
    config = json.load(file)
    if not config:
        print("Config file failed to load")
        quit()

steer = Steering(config, debug=True)
steer.DEBUG_CONTROLLER = True