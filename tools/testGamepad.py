print("To test the gamepad run car.gamepad script")

from evdev import InputDevice, list_devices, ecodes

def describe_event(event):
    type_name = ecodes.EV.get(event.type, f"UNKNOWN({event.type})")

    code_name = "UNKNOWN"
    if event.type in ecodes.bytype:
        code_name = ecodes.bytype[event.type].get(
            event.code, f"UNKNOWN({event.code})"
        )

    return f"{type_name} {code_name} = {event.value}"

try:
    for path in list_devices():
        dev = InputDevice(path)
        print(path, dev.name)
        for event in dev.read_loop():
            if event.type in (ecodes.EV_KEY, ecodes.EV_ABS):
                print(describe_event(event))
except KeyboardInterrupt:
    print("Exiting...")