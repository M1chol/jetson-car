import serial
import threading

port = "/dev/ttyUSB0"


def read_serial():
    while True:
        try:
            data = ser.readline().decode("utf-8", errors="ignore").strip()
            if data:
                print(f"=> {data}")
        except Exception as e:
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
    print("Use CMD<val>;<val> to send angle")
    print("Use BEG to start feedback")
    main()
