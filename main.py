from car.setup import start
from threading import Thread, Event
import argparse
import time
import sys

parser = argparse.ArgumentParser(description="Jetson powered autonomus car")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("--save", action="store_true", help="Save data to persisted file")
parser.add_argument("--dashboard", action="store_true", help="Enable web dashboard")
parser.add_argument("--dashboard-dir", help="pass different media server path")
args = parser.parse_args()

shutdown_event = Event()

def run_car(persist_run, debug):
    try:
        result = start(persistRun=persist_run, debug=debug)
        if not result:
            print("[MAIN] Car setup failed")
    finally:
        print("[MAIN] Car process ended, signaling shutdown")
        shutdown_event.set()

def run_dashboard(media_path, shutdown_event):
    import dashboard as ds
    
    ds.start_media_server(media_path)
    from werkzeug.serving import make_server
    
    server = make_server("0.0.0.0", 5000, ds.app, threaded=True)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Block here until car signals shutdown
    shutdown_event.wait()
    
    print("[DASHBOARD] Shutdown signal received, stopping server")
    ds.mediamtx_process.terminate()
    try:
        ds.mediamtx_process.wait(timeout=5)
        print(f"[DASHBOARD] MediaMTX stopped gracefully")
    except TimeoutError:
        # Force kill if graceful shutdown fails
        ds.mediamtx_process.kill()
        ds.mediamtx_process.wait()
        print(f"[DASHBOARD] MediaMTX force killed")
    
    ds.mediamtx_process = None
    server.shutdown()

if args.dashboard or args.dashboard_dir:
    media_path = args.dashboard_dir if args.dashboard_dir else "/home/m1/Downloads/media"
    car_thread = Thread(target=run_car, args=(args.save, args.debug), daemon=True)
    car_thread.start()
    
    # Start dashboard (blocks until shutdown_event is set)
    run_dashboard(media_path, shutdown_event)
    print("[MAIN] Exiting")
    sys.exit(0)
else:
    if not start(persistRun=args.save, debug=args.debug):
        print("[MAIN] Car setup failed, exiting")