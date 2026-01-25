from car.setup import start
import argparse

parser = argparse.ArgumentParser(description="Jetson powered autonomus car")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("--save", action="store_true", help="Save data to persisted file")
parser.add_argument("--dashboard", action="store_true", help="enable web dashboard")
args = parser.parse_args()
config = None

if not start(persistRun=args.save, debug=args.debug):
    print("[MAIN] Car setup failed, exiting")

if args.dashboard:
    from dashboard import start_dashboard, start_media_server
    start_media_server("/home/m1/Downloads/media")
    start_dashboard()