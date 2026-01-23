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

        abs_caps = dev.capabilities().get(ecodes.EV_ABS, [])

        for item in abs_caps:
            # item may be an int OR a (code, AbsInfo) tuple
            if isinstance(item, tuple):
                code = item[0]
                absinfo = item[1]
            else:
                code = item
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

        for event in dev.read_loop():
            if event.type in (ecodes.EV_KEY, ecodes.EV_ABS):
                print(describe_event(event))

except KeyboardInterrupt:
    print("Exiting...")