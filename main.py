from car.setup import start
from threading import Thread
import argparse

parser = argparse.ArgumentParser(description="Jetson powered autonomus car")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("--save", action="store_true", help="Save data to persisted file")
parser.add_argument("--dashboard", action="store_true", help="to enable web dashboard pass media server path", default="/home/m1/Downloads/media")
args = parser.parse_args()
config = None

if args.dashboard: 
    from dashboard import start_dashboard, start_media_server
    dashboard_thread = Thread(target=start_dashboard, daemon=True)
    start_media_server(args.dashboard)

if not start(persistRun=args.save, debug=args.debug):
    print("[MAIN] Car setup failed, exiting")

