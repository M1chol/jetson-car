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
    main_thread = Thread(target=start, args=(args.save, args.debug), daemon=True)
    main_thread.start()
    import dashboard as ds
    from waitress import serve
    serve(ds.app, host="0.0.0.0", port=5000)
    if args.dashboard_dir:
        ds.start_media_server(args.dashboard_dir)
    else:
        ds.start_media_server("/home/m1/Downloads/media")
else:
    if not start(persistRun=args.save, debug=args.debug):
        print("[MAIN] Car setup failed, exiting")