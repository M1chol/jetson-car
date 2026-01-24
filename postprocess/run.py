import json
import postprocess.data as dt

def run_pipeline(source, timestep, offset):
    with open("car/config.json") as file:
        config = json.load(file)

    wh = config["WHEEL_RADIUS"]
    df = config["DIFF_LENGTH"]

    pathCalculator = dt.WholeFilePathCalculator(
        timestep=timestep,
        wheelRadius=wh,
        diffLength=df,
        offset=offset
    )

    pipeline = dt.DataPipeline(
        dt.CSVLoader(source, timestep=timestep, motorIdsMap=config["MOTOR_IDS_MAP"]),
        [dt.WholeFileInterpolator(), pathCalculator],
        dt.CSVExporter("results/temp/path.csv")
    )

    pipeline.run()
    pipeline.result["order"] = range(len(pipeline.result))

    return pipeline
