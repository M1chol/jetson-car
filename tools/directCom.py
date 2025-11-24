import serial
import threading
import json
from pprint import pprint

port = "/dev/ttyUSB0"

command_map = {
    "CMD_CHANGE_Enable": {"T": 11002, "id": 1},
    "CMD_CHANGE_Disable": {"T": 11003, "id": 1},
    "CMD_DDSM_CTRL": {"T": 10010, "id": 1, "cmd": 50, "act": 3},
    "CMD_DDSM_CHANGE_ID": {"T": 10011, "id": 1},
    "CMD_DDSM_ID_CHECK": {"T": 10031},
    "CMD_CHANGE_MODE": {"T": 10012, "id": 1, "mode": 2},
    "CMD_DDSM_INFO": {"T": 10032, "id": 1},
    "CMD_HEARTBEAT_TIME": {"T": 11001, "time": 2000},
    "CMD_REBOOT": {"T": 600},
}


def generate_command(cmd_name: str, **kwargs) -> str:
    if cmd_name not in command_map:
        raise ValueError(f"Unknown command: {cmd_name}")
    command = command_map[cmd_name].copy()
    command.update(kwargs)
    print(f"[sending] {command}")
    return json.dumps(command)


def read_serial():
    while True:
        try:
            data = ser.readline().decode("utf-8", errors="ignore").strip()
            if data:
                print(f"=> {data}")
        except Exception:
            # Optional: log or break if needed
            pass


def main():
    global ser

    ser = serial.Serial(port, baudrate=115200, timeout=1, dsrdtr=False, rtscts=False)
    ser.setRTS(False)
    ser.setDTR(False)

    serial_recv_thread = threading.Thread(target=read_serial, daemon=True)
    serial_recv_thread.start()

    try:
        while True:
            command = input("")
            ser.write(command.encode() + b"\n")
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


if __name__ == "__main__":
    print("[SERVO] Use CMD<val>;<val> to send angle")
    print("[SERVO] Use BEG to start feedback")
    print("[SERVO] Use CAL to calibrate servos center position")
    print("[SERVO] Use STP to stop feedback")
    print("[MOTOR] Use '>' symbol and provide command name to generate commands")
    pprint(command_map)
    main()
