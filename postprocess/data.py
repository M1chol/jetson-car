import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any
from threading import Event


class Loader:
    def load(self) -> pd.DataFrame:
        ...


class Transformer:
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        ...


class Exporter:
    def export(self, data: pd.DataFrame) -> None:
        ...


class DataPipeline:
    def __init__(
        self, loader: Loader, transformers: list[Transformer], exporter: Exporter
    ):
        self.loader = loader
        self.transformers = transformers
        self.exporter = exporter
        self.source: pd.DataFrame = pd.DataFrame()
        self.result: pd.DataFrame = pd.DataFrame()

    def run(self):
        self.source = self.loader.load()
        data = self.source
        for transformer in self.transformers:
            data = transformer.transform(data)
        self.result = data
        self.exporter.export(data)

    def run_stream(self, stop_event: Event):
        while not stop_event.is_set():
            data = self.loader.load()
            self.source = pd.concat([self.source, data], ignore_index=True)
            for transformer in self.transformers:
                data = transformer.transform(data)
            self.result = pd.concat([self.result, data], ignore_index=True)


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


class CSVLoader(Loader):
    def __init__(self, fileIn: Path, timestep: float, motorIdsMap):
        self.fileIn = fileIn
        self.timestep = timestep
        self.motorIdsMap = motorIdsMap

    def load(self) -> pd.DataFrame:
        timeline = {}
        keys = list(empty_record().keys())
        with open(self.fileIn, "r") as f:
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
                ts = time // self.timestep

                if ts not in timeline:
                    timeline[ts] = empty_record()

                if entry["type"] == "MOTOR":
                    motor = self.motorIdsMap.index(entry["data"]["id"])
                    motor *= 3

                    if not timeline[ts][keys[motor]]:
                        timeline[ts][keys[motor]] = entry["data"]["spd"]
                    else:
                        timeline[ts][keys[motor]] = (
                            entry["data"]["spd"] + timeline[ts][keys[motor]]
                        ) / 2

                    if not timeline[ts][keys[motor + 1]]:
                        timeline[ts][keys[motor + 1]] = entry["data"]["crt"]
                    else:
                        timeline[ts][keys[motor + 1]] = (
                            entry["data"]["crt"] + timeline[ts][keys[motor + 1]]
                        ) / 2

                    if not timeline[ts][keys[motor + 2]]:
                        timeline[ts][keys[motor + 2]] = entry["data"]["act"]
                    else:
                        timeline[ts][keys[motor + 2]] = (
                            entry["data"]["act"] + timeline[ts][keys[motor + 2]]
                        ) / 2

                elif entry["type"] == "SERVO":
                    if not timeline[ts]["angle_front"]:
                        timeline[ts]["angle_front"] = float(entry["data"]["servo_2"])
                    else:
                        timeline[ts]["angle_front"] = (
                            float(entry["data"]["servo_2"]) + timeline[ts]["angle_front"]
                        ) / 2

                    if not timeline[ts]["angle_rear"]:
                        timeline[ts]["angle_rear"] = float(entry["data"]["servo_1"])
                    else:
                        timeline[ts]["angle_rear"] = (
                            float(entry["data"]["servo_1"]) + timeline[ts]["angle_rear"]
                        ) / 2

        result = pd.DataFrame.from_dict(timeline, orient="index")
        result = result.reset_index().rename(columns={"index": "timestep"})
        result = result.sort_values("timestep").reset_index(drop=True)
        return result


class WholeFileInterpolator(Transformer):
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.interpolate()
        while not data.empty and data.iloc[0].isna().any():
            data = data.iloc[1:]
        return data


class WholeFilePathCalculator(Transformer):
    def __init__(self, timestep: float, wheelRadius: float, diffLength: float, offset: float):
        self.timestep = timestep
        self.wheelRadius = wheelRadius
        self.diffLength = diffLength
        self.offset = offset

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        data["speed_mean"] = (
            -data["speed_front_right"]
            - data["speed_rear_right"]
            + data["speed_rear_left"]
            + data["speed_front_left"]
        ) / 4
        data["speed_mps_mean"] = (
            data["speed_mean"] / 10 * 2 * np.pi * self.wheelRadius / 60
        )
        x, y, theta = 0.0, 0.0, 0.0
        data["angle_mean"] = (data["angle_front"] - data["angle_rear"]) / 2 + self.offset
        data["angle_mean_rad"] = np.deg2rad(data["angle_mean"])
        pos_x = []
        pos_y = []
        for _, row in data.iterrows():
            theta += (
                row["speed_mps_mean"]
                / self.diffLength
                * 2
                * self.timestep
                * np.tan(row["angle_mean_rad"])
            )
            x += row["speed_mps_mean"] * np.cos(theta) * self.timestep
            y += row["speed_mps_mean"] * np.sin(theta) * self.timestep
            pos_x.append(x)
            pos_y.append(y)

        path = pd.DataFrame(
            {
                "pos_x": pos_x,
                "pos_y": pos_y,
                "current_speed": data["speed_mps_mean"],
                "current_angle": data["angle_mean_rad"],
                "timestep": data["timestep"],
            }
        )

        return path


class CSVExporter(Exporter):
    def __init__(self, fileOut):
        self.fileOut = fileOut

    def export(self, data: pd.DataFrame):
        data.to_csv(self.fileOut, index=False)