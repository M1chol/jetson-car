from car.setup import start
import argparse

parser = argparse.ArgumentParser(description="Jetson powered autonomus car")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("--save", action="store_true", help="Save data to persisted file")
args = parser.parse_args()
config = None

if not start(persistRun=args.save, debug=args.debug):
    print("[MAIN] Car setup failed, exiting")