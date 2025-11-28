# TODO: Integrate to the pipeline

import json
import csv
import pandas as pd
import numpy as np

TIMESTEP = 0.1

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
            "angle_front": None,
            "angle_rear": None,
        }

def normalizeData(fileIn: str, fileOut: str) -> None:
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
                if not timeline[ts]["angle_front"]:
                    timeline[ts]["angle_front"] = float(entry["data"]["servo_2"])
                else:
                    timeline[ts]["angle_front"] = (float(entry["data"]["servo_2"]) + timeline[ts]["angle_front"]) / 2
                
                if not timeline[ts]["angle_rear"]:
                    timeline[ts]["angle_rear"] = float(entry["data"]["servo_1"])
                else:
                    timeline[ts]["angle_rear"] =(float(entry["data"]["servo_1"]) + timeline[ts]["angle_rear"]) / 2
                
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
    while not df.empty and df.iloc[0].isna().any():
        df = df.iloc[1:]
    df.to_csv(fileOut, index=False)
    print(f"Interpolate done. CSV saved to: {fileOut}")

def calculatePath(fileIn: str, fileOut: str) -> None:
    df = pd.read_csv(fileIn)
    df["speed_mean"] = (- df["speed_front_right"] - df["speed_rear_right"] + df["speed_rear_left"] + df["speed_front_left"]) / 4
    df["speed_mps_mean"] = df["speed_mean"] / 10 * 2 * np.pi * config["WHEEL_RADIUS"] / 60
    x, y, theta = 0.0, 0.0, 0.0
    df["angle_mean"] = (df["angle_front"] - df["angle_rear"]) / 2 + 1
    df["angle_mean_rad"] = np.deg2rad(df["angle_mean"])
    pos_x = []
    pos_y = []
    for _, row in df.iterrows():
        # v / L * 2 * dt * tan()
        theta += row["speed_mps_mean"] / config["DIFF_LENGTH"] * 2 * TIMESTEP * np.tan(row["angle_mean_rad"])
        x += row["speed_mps_mean"] * np.cos(theta) * TIMESTEP
        y += row["speed_mps_mean"] * np.sin(theta) * TIMESTEP
        pos_x.append(x)
        pos_y.append(y)

    path = pd.DataFrame({
        "pos_x": pos_x,
        "pos_y": pos_y,
        "current_speed": df["speed_mps_mean"],
        "current_angle": df["angle_mean_rad"],
        "timestep": df["timestep"]
    })

    path.to_csv(fileOut, index=False)

if __name__ == "__main__":
    normalizeData("results/2025-11-25/out.txt", "results/2025-11-25/normalized.csv")
    interpolate("results/2025-11-25/normalized.csv", "results/2025-11-25/interpolated.csv")
    calculatePath("results/2025-11-25/interpolated.csv", "results/2025-11-25/path.csv")