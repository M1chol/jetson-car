import argparse
import postprocess.data as dt
import json
import os

parser = argparse.ArgumentParser(description="Jetson powered autonomus car")
parser.add_argument("--timestep", "-t", action="store_const", help="set timestep, default 0.1", default=0.1, const=0.1)
parser.add_argument("--source", "-s", action="store_const", help="source folder where out.txt is located", default="results/temp/out.txt", const="results/temp/out.txt")
parser.add_argument('--offset', '-o', action='store_const', help="set offset for calculating path", default=0, const=0)
args = parser.parse_args()

IS_STREAMLIT = "streamlit" in os.environ.get("_")

with open("car/config.json") as file:
    config = json.load(file)
    if not config:
        print("[DATA] Config file failed to load")
        quit()

wh = config["WHEEL_RADIUS"]
df = config["DIFF_LENGTH"]

if IS_STREAMLIT:
    import streamlit as st
    import altair as alt

    if "offset" not in st.session_state:
        st.session_state.offset = 1.0

    st.title("Wyznaczona trasa")
    
    offset_val = st.slider("Offset", -2.0, 2.0, st.session_state.offset, 0.05)
    
    if st.button("Rerun"):
        st.session_state.offset = offset_val
        st.rerun()
    
    pathCalculator = dt.WholeFilePathCalculator(
        timestep=args.timestep, 
        wheelRadius=wh, 
        diffLength=df, 
        offset=st.session_state.offset
    )

    pipeline = dt.DataPipeline(
        dt.CSVLoader(args.source, timestep=args.timestep, motorIdsMap=config["MOTOR_IDS_MAP"]),
        [dt.WholeFileInterpolator(), pathCalculator],
        dt.CSVExporter("results/temp/path.csv")
    )

    pipeline.run()
    pipeline.result["order"] = range(len(pipeline.result))

    min_val = min(pipeline.result['pos_x'].min(), pipeline.result['pos_y'].min())
    max_val = max(pipeline.result['pos_x'].max(), pipeline.result['pos_y'].max())

    chart = (
        alt.Chart(pipeline.result).mark_line() + alt.Chart(pipeline.result).mark_point()
    ).encode(
        x=alt.X('pos_x:Q', scale=alt.Scale(domain=[min_val, max_val])),
        y=alt.Y('pos_y:Q', scale=alt.Scale(domain=[min_val, max_val])),
        order='order:O',
        tooltip=['order', 'pos_x', 'pos_y']
    ).properties(width=800, height=600)

    st.altair_chart(chart, width="stretch")
    st.title("Wykresy przebiegu")
    st.write("Wykres średniej prędkości")
    st.line_chart(pipeline.result, x="timestep", y="current_speed")
    st.write("Wykres średniego kątu skrętu")
    st.line_chart(pipeline.result, x="timestep", y="current_angle")
    st.write("Wykres wszystkich kątów")
    st.line_chart(pipeline.source, x="timestep", y=["angle_front", "angle_rear"])
    st.write("Wykres wszystkich prędkości")
    st.line_chart(pipeline.source, x="timestep", y=["speed_front_right", "speed_rear_right", "speed_rear_left", "speed_front_left"])

else:
    of = 1
    pathCalculator = dt.WholeFilePathCalculator(timestep=args.timestep, wheelRadius=wh, diffLength=df, offset=of)
    pipeline = dt.DataPipeline(
        dt.CSVLoader(args.source, timestep=args.timestep, motorIdsMap=config["MOTOR_IDS_MAP"]),
        [dt.WholeFileInterpolator(), pathCalculator],
        dt.CSVExporter("results/temp/path.csv")
    )
    pipeline.run()