print("To test the gamepad run car.gamepad script")

from evdev import InputDevice, list_devices, ecodes

for path in list_devices():
    dev = InputDevice(path)
    print(path, dev.name)
    for event in dev.read_loop():
        if event.type in (ecodes.EV_KEY, ecodes.EV_ABS):
            print(event)