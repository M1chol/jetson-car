import matplotlib.pyplot as plt
import pandas as pd

def load(fileIn: str):
    return pd.read_csv(fileIn)

def drawSpeed(interpolated, raw):
    fig, ax = plt.subplots(2, 2, figsize=(10, 6))

    ax[1, 1].plot(interpolated["timestep"], interpolated["speed_rear_right"], marker="o", markersize=2)
    ax[1, 1].scatter(raw["timestep"], raw["speed_rear_right"], s=10, color="tab:red")
    ax[1, 1].set_title("Speed Rear Right")
    
    ax[0, 1].plot(interpolated["timestep"], interpolated["speed_front_right"], marker="o", markersize=2)
    ax[0, 1].scatter(raw["timestep"], raw["speed_front_right"], s=10, color="tab:red")
    ax[0, 1].set_title("Speed Front Right")

    ax[1, 0].plot(interpolated["timestep"], interpolated["speed_rear_left"], marker="o", markersize=2)
    ax[1, 0].scatter(raw["timestep"], raw["speed_rear_left"], s=10, color="tab:red")
    ax[1, 0].set_title("Speed Rear Left")

    ax[0, 0].plot(interpolated["timestep"], interpolated["speed_front_left"], marker="o", markersize=2)
    ax[0, 0].scatter(raw["timestep"], raw["speed_front_left"], s=10, color="tab:red")
    ax[0, 0].set_title("Speed Front Left")

    # Set axis labels for all subplots
    for axes in ax.flat:
        axes.set_xlabel("Timestep")
        axes.set_ylabel("Speed")

    fig.tight_layout()
    plt.show()

def drawCurrent(interpolated, raw):
    fig, ax = plt.subplots(2, 2, figsize=(10, 6))

    ax[1, 1].plot(interpolated["timestep"], interpolated["current_rear_right"], marker="o", markersize=2)
    ax[1, 1].scatter(raw["timestep"], raw["current_rear_right"], s=10, color="tab:red")
    ax[1, 1].set_title("Current Rear Right")

    ax[0, 1].plot(interpolated["timestep"], interpolated["current_front_right"], marker="o", markersize=2)
    ax[0, 1].scatter(raw["timestep"], raw["current_front_right"], s=10, color="tab:red")
    ax[0, 1].set_title("Current Front Right")

    ax[1, 0].plot(interpolated["timestep"], interpolated["current_rear_left"], marker="o", markersize=2)
    ax[1, 0].scatter(raw["timestep"], raw["current_rear_left"], s=10, color="tab:red")
    ax[1, 0].set_title("Current Rear Left")

    ax[0, 0].plot(interpolated["timestep"], interpolated["current_front_left"], marker="o", markersize=2)
    ax[0, 0].scatter(raw["timestep"], raw["current_front_left"], s=10, color="tab:red")
    ax[0, 0].set_title("Current Front Left")

    # Set axis labels for all subplots
    for axes in ax.flat:
        axes.set_xlabel("Timestep")
        axes.set_ylabel("Current")

    fig.tight_layout()
    plt.show()


def drawAngle(interpolated, raw):
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))

    ax[0].plot(interpolated["timestep"], interpolated["front_angle"], marker="o", markersize=2)
    ax[0].scatter(raw["timestep"], raw["front_angle"], s=10, color="tab:red")
    ax[0].set_title("Front Angle")

    ax[1].plot(interpolated["timestep"], interpolated["back_angle"], marker="o", markersize=2)
    ax[1].scatter(raw["timestep"], raw["back_angle"], s=10, color="tab:red")
    ax[1].set_title("Back Angle")

    # Set axis labels for both subplots
    for axes in ax.flat:
        axes.set_xlabel("Timestep")
        axes.set_ylabel("Angle")

    fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    interpolated = load("results/2025-11-24/interpolated.csv")
    raw = load("results/2025-11-24/normalized.csv")
    drawSpeed(interpolated, raw)
    drawCurrent(interpolated, raw)
    drawAngle(interpolated, raw)