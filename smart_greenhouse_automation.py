"""
Smart Greenhouse IoT Automation System
Task 4: IoT Automation Logic
Internship Project - DecodeLabs IoT Track

Description:
    Simulates a smart greenhouse that reads environmental sensor data
    (temperature, soil moisture, light intensity, humidity) and applies
    rule-based automation logic to control actuators (fan, irrigation,
    grow-lights, heater).  All automation events are logged to a file
    and displayed in a summary chart at the end of the session.

Author: [Your Name]
Date: 2025
"""

import random
import time
import csv
import os
import datetime
import threading
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import deque

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
POLL_INTERVAL   = 2          # seconds between sensor reads
RUNTIME_SECONDS = 90         # total simulation runtime
MAX_HISTORY     = 40         # data points kept for chart
LOG_FILE        = "greenhouse_automation_log.csv"

# Sensor normal operating ranges
SENSOR_RANGES = {
    "temperature":    (15.0, 40.0),   # °C
    "soil_moisture":  (20,   90),      # % (100 = saturated)
    "light_intensity":(100,  900),     # lux
    "humidity":       (40,   90),      # %
}

# Automation rule thresholds
RULES = {
    # sensor           : (condition,  threshold,  actuator,    action_label)
    "temp_high"        : ("above",    32.0,       "Fan",       "ON  ─ Cooling"),
    "temp_normal"      : ("below",    28.0,       "Fan",       "OFF ─ Idle"),
    "temp_low"         : ("below",    18.0,       "Heater",    "ON  ─ Warming"),
    "heater_off"       : ("above",    20.0,       "Heater",    "OFF ─ Idle"),
    "dry_soil"         : ("below",    35,         "Irrigation","ON  ─ Watering"),
    "wet_soil"         : ("above",    75,         "Irrigation","OFF ─ Stopped"),
    "low_light"        : ("below",    200,        "Grow-Lights","ON  ─ Supplementing"),
    "high_light"       : ("above",    800,        "Grow-Lights","OFF ─ Natural"),
    "high_humidity"    : ("above",    80,         "Vent",      "OPEN ─ Venting"),
    "ok_humidity"      : ("below",    70,         "Vent",      "CLOSED ─ Sealed"),
}

# ─────────────────────────────────────────────
#  SHARED STATE
# ─────────────────────────────────────────────
sensor_history = {s: deque(maxlen=MAX_HISTORY) for s in SENSOR_RANGES}
actuator_states = {
    "Fan":         "OFF",
    "Heater":      "OFF",
    "Irrigation":  "OFF",
    "Grow-Lights": "OFF",
    "Vent":        "CLOSED",
}
automation_events = []   # list of (timestamp, actuator, action, sensor, value)
data_lock  = threading.Lock()
running    = True

# ─────────────────────────────────────────────
#  SENSOR SIMULATION
# ─────────────────────────────────────────────
def simulate_sensors():
    """Return one reading per sensor with realistic drift and occasional spikes."""
    readings = {}
    for sensor, (lo, hi) in SENSOR_RANGES.items():
        # 15 % chance of an out-of-range spike to test automation
        if random.random() < 0.15:
            spike_dir = random.choice([-1, 1])
            span = hi - lo
            if isinstance(lo, float):
                val = round(random.uniform(
                    lo + spike_dir * span * 0.2,
                    hi + spike_dir * span * 0.2), 1)
            else:
                val = random.randint(
                    int(lo + spike_dir * span * 0.2),
                    int(hi + spike_dir * span * 0.2))
        else:
            if isinstance(lo, float):
                val = round(random.uniform(lo, hi), 1)
            else:
                val = random.randint(lo, hi)
        readings[sensor] = val
    return readings


# ─────────────────────────────────────────────
#  AUTOMATION ENGINE
# ─────────────────────────────────────────────
def evaluate_rules(readings):
    """
    Apply all automation rules against current sensor readings.
    Returns list of (actuator, new_state, trigger_sensor, value).
    """
    changes = []
    temp  = readings["temperature"]
    moist = readings["soil_moisture"]
    light = readings["light_intensity"]
    hum   = readings["humidity"]

    # ── Temperature rules ──────────────────────────
    if temp > RULES["temp_high"][1]:
        changes.append(("Fan", RULES["temp_high"][3], "temperature", temp))
    elif temp < RULES["temp_normal"][1]:
        changes.append(("Fan", RULES["temp_normal"][3], "temperature", temp))

    if temp < RULES["temp_low"][1]:
        changes.append(("Heater", RULES["temp_low"][3], "temperature", temp))
    elif temp > RULES["heater_off"][1]:
        changes.append(("Heater", RULES["heater_off"][3], "temperature", temp))

    # ── Soil moisture rules ────────────────────────
    if moist < RULES["dry_soil"][1]:
        changes.append(("Irrigation", RULES["dry_soil"][3], "soil_moisture", moist))
    elif moist > RULES["wet_soil"][1]:
        changes.append(("Irrigation", RULES["wet_soil"][3], "soil_moisture", moist))

    # ── Light rules ────────────────────────────────
    if light < RULES["low_light"][1]:
        changes.append(("Grow-Lights", RULES["low_light"][3], "light_intensity", light))
    elif light > RULES["high_light"][1]:
        changes.append(("Grow-Lights", RULES["high_light"][3], "light_intensity", light))

    # ── Humidity rules ─────────────────────────────
    if hum > RULES["high_humidity"][1]:
        changes.append(("Vent", RULES["high_humidity"][3], "humidity", hum))
    elif hum < RULES["ok_humidity"][1]:
        changes.append(("Vent", RULES["ok_humidity"][3], "humidity", hum))

    return changes


def apply_changes(changes, timestamp):
    """Update actuator states and log any state change."""
    for actuator, new_state, trigger_sensor, value in changes:
        old_state = actuator_states[actuator]
        actuator_states[actuator] = new_state
        if old_state != new_state:
            msg = (f"  [{timestamp}] ⚙  {actuator:<14} → {new_state}"
                   f"  (trigger: {trigger_sensor}={value})")
            print(msg)
            automation_events.append(
                (timestamp, actuator, new_state, trigger_sensor, value))

            with open(LOG_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, actuator, new_state,
                                 trigger_sensor, value])


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def iot_loop():
    """Sensor polling + rule evaluation + actuator control loop."""
    global running

    # Initialise log file
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "actuator", "new_state",
                         "trigger_sensor", "sensor_value"])

    start = time.time()
    while running and (time.time() - start) < RUNTIME_SECONDS:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        readings  = simulate_sensors()

        with data_lock:
            for sensor, value in readings.items():
                sensor_history[sensor].append(value)

        print(f"\n[{timestamp}] Sensor Readings:")
        print(f"  Temp={readings['temperature']}°C  "
              f"Moisture={readings['soil_moisture']}%  "
              f"Light={readings['light_intensity']} lux  "
              f"Humidity={readings['humidity']}%")
        print("  Actuator Status: " +
              " | ".join(f"{k}: {v}" for k, v in actuator_states.items()))

        changes = evaluate_rules(readings)
        apply_changes(changes, timestamp)

        time.sleep(POLL_INTERVAL)

    running = False


# ─────────────────────────────────────────────
#  FINAL REPORT CHART
# ─────────────────────────────────────────────
def show_report():
    """Generate a 4-panel summary chart of sensor readings over the session."""
    sensors = list(SENSOR_RANGES.keys())
    labels  = {
        "temperature":    "Temperature (°C)",
        "soil_moisture":  "Soil Moisture (%)",
        "light_intensity":"Light Intensity (lux)",
        "humidity":       "Humidity (%)",
    }
    threshold_high = {
        "temperature":    32.0,
        "soil_moisture":  75,
        "light_intensity":800,
        "humidity":       80,
    }
    threshold_low = {
        "temperature":    18.0,
        "soil_moisture":  35,
        "light_intensity":200,
        "humidity":       None,
    }
    colors = ["#ef9f76", "#a6d189", "#e5c890", "#8caaee"]

    fig = plt.figure(figsize=(14, 8), facecolor="#1e1e2e")
    fig.suptitle("Smart Greenhouse — Session Summary",
                 fontsize=14, fontweight="bold", color="white")
    gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    for idx, sensor in enumerate(sensors):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        ax.set_facecolor("#181825")
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#45475a")

        data = list(sensor_history[sensor])
        ax.plot(data, color=colors[idx], linewidth=2, label=labels[sensor])

        ax.axhline(y=threshold_high[sensor], color="#e78284",
                   linestyle="--", alpha=0.7, linewidth=1, label="High threshold")
        if threshold_low[sensor] is not None:
            ax.axhline(y=threshold_low[sensor], color="#85c1dc",
                       linestyle="--", alpha=0.7, linewidth=1, label="Low threshold")

        ax.set_title(labels[sensor], color="white", fontsize=10, pad=5)
        ax.set_xlabel("Sample #", color="#6c7086", fontsize=8)
        ax.legend(fontsize=7, facecolor="#313244", labelcolor="white",
                  loc="upper left")
        ax.grid(True, color="#313244", linestyle="--", linewidth=0.5)

    plt.savefig("greenhouse_session_report.png", dpi=120,
                bbox_inches="tight", facecolor="#1e1e2e")
    plt.show()
    print("[INFO] Chart saved to greenhouse_session_report.png")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    global running

    print("=" * 60)
    print("  Smart Greenhouse IoT Automation System")
    print(f"  Runtime: {RUNTIME_SECONDS}s | Poll interval: {POLL_INTERVAL}s")
    print(f"  Automation log: {LOG_FILE}")
    print("=" * 60)
    print("\nActuators: Fan | Heater | Irrigation | Grow-Lights | Vent")
    print("Starting sensor loop...\n")

    iot_thread = threading.Thread(target=iot_loop, daemon=True)
    iot_thread.start()

    try:
        iot_thread.join()
    except KeyboardInterrupt:
        running = False
        print("\n[INFO] Interrupted by user.")

    print("\n" + "=" * 60)
    print(f"  Session complete — {len(automation_events)} automation event(s)")
    print("=" * 60)

    for ts, act, state, sensor, val in automation_events[-10:]:
        print(f"  {ts}  {act:<14} → {state}  ({sensor}={val})")

    print("\n[INFO] Generating session report chart...")
    show_report()
    print(f"[INFO] Full log saved to '{LOG_FILE}'")


if __name__ == "__main__":
    main()
