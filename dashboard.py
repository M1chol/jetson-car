from flask import Flask, render_template, jsonify
from postprocess.run import run_pipeline

app = Flask(__name__)
pipeline = None

def start_media_server(server_location):
    import subprocess

    def is_mediamtx_running():
        result = subprocess.run(
            ["pgrep", "-f", "mediamtx"],
            stdout=subprocess.DEVNULL
        )
        return result.returncode == 0

    if not is_mediamtx_running():
        proc = subprocess.Popen(
            ["./mediamtx"],
            cwd=server_location
        )
        print(f"[DASHBOARD] MediaMTX started {proc.pid}")
    else:
        print("[DASHBOARD] MediaMTX is already running")


@app.route("/")
def index():   
    return render_template("dashboard.html")

def multiline_data(df, x, y, series_name="series"):
    subset = df[[x] + y].copy()
    melted = subset.melt(
        id_vars=[x],
        value_vars=y,
        var_name=series_name,
        value_name="y"
    )
    melted.rename(columns={x: "x"}, inplace=True)
    melted = melted.dropna(subset=["y"])
    return melted.to_dict("records")

@app.route("/run/<timestep>/<offset>/<path:run_id>", methods=["POST"])
def run(timestep, offset, run_id):
    global pipeline
    pipeline = run_pipeline(run_id, timestep=float(timestep), offset=float(offset))
    return "Pipeline executed."

@app.route("/postprocess")
def postprocess():   
    return render_template("postprocess.html")

@app.route("/data/speed")
def speed():
    global pipeline
    if not pipeline:
        return jsonify([])
    return jsonify(multiline_data(
        pipeline.result,
        x="timestep",
        y=["current_speed"],
    ))

@app.route("/data/angle")
def angle():
    global pipeline
    if not pipeline:
        return jsonify([])
    return jsonify(multiline_data(
        pipeline.result,
        x="timestep",
        y=["current_angle"],
    ))

@app.route("/data/angles")
def angles():
    global pipeline
    if not pipeline:
        return jsonify([])
    return jsonify(multiline_data(
        pipeline.source,
        x="timestep",
        y=["angle_front", "angle_rear"],
        series_name="location"
    ))

@app.route("/data/speeds")
def speeds():
    global pipeline
    if not pipeline:
        return jsonify([])
    return jsonify(multiline_data(
        pipeline.source,
        x="timestep",
        y=["speed_front_right", "speed_rear_right", "speed_rear_left", "speed_front_left"],
        series_name="wheel"
    ))

@app.route("/data/path")
def path():
    global pipeline
    if not pipeline:
        return jsonify([])
    x = pipeline.result['pos_x']
    y = pipeline.result['pos_y']
    t = pipeline.result['timestep']
    return jsonify([{"x": xi, "y": yi, "t": ti} for xi, yi, ti in zip(x, y, t)])

if __name__ == "__main__":
    app.run(host="0.0.0.0")
