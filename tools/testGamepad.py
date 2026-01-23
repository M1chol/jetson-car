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

        for code in dev.capabilities().get(ecodes.EV_ABS, []):
            absinfo = dev.absinfo(code)
            axis_name = ecodes.ABS.get(code, f"ABS_{code}")

            print(
                f"{axis_name}: "
                f"min={absinfo.min}, "
                f"max={absinfo.max}, "
                f"value={absinfo.value}, "
                f"flat={absinfo.flat}, "
                f"fuzz={absinfo.fuzz}, "
                f"res={absinfo.resolution}"
            )
            print(f"Calculated config values for {axis_name}: ")
            print(f"PAD_READ_CENTER = {absinfo.value}")
            print(f"PAD_READ_X = {absinfo.max - absinfo.min}")

        for event in dev.read_loop():
            if event.type in (ecodes.EV_KEY, ecodes.EV_ABS):
                print(describe_event(event))

except KeyboardInterrupt:
    print("Exiting...")