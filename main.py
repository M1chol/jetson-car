from car.setup import start
from threading import Thread
import argparse

parser = argparse.ArgumentParser(description="Jetson powered autonomus car")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("--save", action="store_true", help="Save data to persisted file")
parser.add_argument("--dashboard", action="store_true", help="Enable web dashboard default media path /home/m1/Downloads/media")
parser.add_argument("--dashboard-dir", help="pass different media server path")
args = parser.parse_args()
config = None

if args.dashboard: 
    import dashboard as ds
    dashboard_thread = Thread(target=ds.start_dashboard, daemon=True)
    if args.dashboard_dir:
        ds.start_media_server(args.dashboard_dir)
    else:
        ds.start_media_server("/home/m1/Downloads/media")

if not start(persistRun=args.save, debug=args.debug):
    print("[MAIN] Car setup failed, exiting")