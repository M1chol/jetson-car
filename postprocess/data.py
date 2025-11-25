# TODO: Integrate to the pipeline

import json
import csv
import pandas as pd

# Load config
print("[CAR] Loading config file...")
with open("car/config.json") as file:
    config = json.load(file)
    if not config:
        print("[CAR] Config file failed to load")
        quit()

def empty_record():
        return {
            "speed_front_right": None,
            "current_front_right": None,
            "acceleration_front_right": None,
            "speed_rear_right": None,
            "current_rear_right": None,
            "acceleration_rear_right": None,
            "speed_rear_left": None,
            "current_rear_left": None,
            "acceleration_rear_left": None,
            "speed_front_left": None,
            "current_front_left": None,
            "acceleration_front_left": None,
            "front_angle": None,
            "back_angle": None,
        }

def normalizeData(fileIn: str, fileOut: str) -> None:
    TIMESTEP = 0.02
    timeline = {}
    keys = list(empty_record().keys())
    with open(fileIn, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except:
                print("[NORMALIZER] WARN Skipping malformed line:", line)
                continue
            
            time = float(entry["time"])
            ts = time // TIMESTEP

            if ts not in timeline:
                timeline[ts] = empty_record()
            
            if entry["type"] == "MOTOR":
                motor = config["MOTOR_IDS_MAP"].index(entry["data"]["id"])
                motor*=3 # Align the id with labels speed, current, acceleration for each motor
                
                if not timeline[ts][keys[motor]]:
                    timeline[ts][keys[motor]] = entry["data"]["spd"]
                else:
                    timeline[ts][keys[motor]] = (entry["data"]["spd"] + timeline[ts][keys[motor]]) / 2
                
                if not timeline[ts][keys[motor+1]]:
                    timeline[ts][keys[motor+1]] = entry["data"]["crt"]
                else:
                    timeline[ts][keys[motor+1]] = (entry["data"]["crt"] + timeline[ts][keys[motor+1]]) / 2

                if not timeline[ts][keys[motor+2]]:
                    timeline[ts][keys[motor+2]] = entry["data"]["act"]
                else:
                    timeline[ts][keys[motor+2]] = (entry["data"]["act"] + timeline[ts][keys[motor+2]]) / 2

            elif entry["type"] == "SERVO":
                if not timeline[ts]["front_angle"]:
                    timeline[ts]["front_angle"] = float(entry["data"]["servo_2"])
                else:
                    timeline[ts]["front_angle"] = (float(entry["data"]["servo_2"]) + timeline[ts]["front_angle"]) / 2
                
                if not timeline[ts]["back_angle"]:
                    timeline[ts]["back_angle"] = float(entry["data"]["servo_1"])
                else:
                    timeline[ts]["back_angle"] =(float(entry["data"]["servo_1"]) + timeline[ts]["back_angle"]) / 2
                
    with open(fileOut, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["timestep"] + list(empty_record().keys()))
        writer.writeheader()

        for ts in sorted(timeline.keys()):
            row = timeline[ts]
            row["timestep"] = ts
            writer.writerow(row)

    print(f"Normalization done. CSV saved to: {fileOut}")
                

def interpolate(fileIn: str, fileOut: str) -> None:
    df = pd.read_csv(fileIn)
    df = df.interpolate()
    df.to_csv(fileOut, index=False)
    print(f"Interpolate done. CSV saved to: {fileOut}")

if __name__ == "__main__":
    normalizeData("results/2025-11-24/out.txt", "results/2025-11-24/normalized.csv")
    interpolate("results/2025-11-24/normalized.csv", "results/2025-11-24/interpolated.csv")