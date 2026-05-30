#  Smart Greenhouse IoT Automation System
### IoT Internship Project — Task 4: IoT Automation Logic
**DecodeLabs IoT Internship Track**

---

##  Project Overview

This project implements a rule-based IoT Automation System for a smart greenhouse. Environmental sensors (temperature, soil moisture, light intensity, humidity) are continuously polled. Automation rules evaluate every reading and trigger actuators (fan, heater, irrigation pump, grow-lights, ventilation vent) to maintain optimal growing conditions automatically.

This fulfillsthe following requirements:
-  Define conditions (e.g., `temperature > 32°C → Fan ON`)
-  Trigger alerts / actions based on sensor data
-  Display automation results (console + session summary chart)

---

##  System Architecture

```
Sensor Simulation Layer
  └─ Temperature / Soil Moisture / Light / Humidity generators
        │
        ▼
Automation Engine  ← Reads sensor values
  └─ 10 rule definitions evaluated every cycle
  └─ Computes required actuator state changes
        │
        ▼
Actuator Controller
  └─ Fan | Heater | Irrigation | Grow-Lights | Vent
  └─ Logs every state change to CSV
        │
        ▼
Session Report
  └─ 4-panel sensor history chart saved as PNG
  └─ Automation event summary printed to console
```

---

##  Automation Rules

| Condition | Sensor | Threshold | Action |
|-----------|--------|-----------|--------|
| Too hot | Temperature | > 32 °C | Fan **ON** |
| Temperature normal | Temperature | < 28 °C | Fan **OFF** |
| Too cold | Temperature | < 18 °C | Heater **ON** |
| Warmed up | Temperature | > 20 °C | Heater **OFF** |
| Dry soil | Soil Moisture | < 35 % | Irrigation **ON** |
| Soil saturated | Soil Moisture | > 75 % | Irrigation **OFF** |
| Low light | Light Intensity | < 200 lux | Grow-Lights **ON** |
| Bright enough | Light Intensity | > 800 lux | Grow-Lights **OFF** |
| High humidity | Humidity | > 80 % | Vent **OPEN** |
| Humidity OK | Humidity | < 70 % | Vent **CLOSED** |

---

##  Technologies Used

| Tool | Purpose |
|------|---------|
| Python 3.x | Core language |
| `threading` | Concurrent sensor loop |
| `matplotlib` | Session report chart |
| `csv` / `os` | Event logging |
| `random` | Sensor simulation with anomalies |
| `collections.deque` | Rolling sensor history |

---

## 🚀 Getting Started

### Prerequisites
```bash
pip install matplotlib
```

### Run the automation system
```bash
python smart_greenhouse_automation.py
```

The system runs for 90 seconds (configurable), printing sensor readings and actuator decisions every 2 seconds. A summary chart is generated at the end.

---

##  Sample Console Output

```
[10:05:02] Sensor Readings:
  Temp=34.1°C  Moisture=28%  Light=145 lux  Humidity=83%
  Actuator Status: Fan: OFF | Heater: OFF | Irrigation: OFF | Grow-Lights: OFF | Vent: CLOSED

  [10:05:02] ⚙  Fan            → ON  ─ Cooling  (trigger: temperature=34.1)
  [10:05:02] ⚙  Irrigation     → ON  ─ Watering  (trigger: soil_moisture=28)
  [10:05:02] ⚙  Grow-Lights    → ON  ─ Supplementing  (trigger: light_intensity=145)
  [10:05:02] ⚙  Vent           → OPEN ─ Venting  (trigger: humidity=83)
```

---

##  Output Files

| File | Description |
|------|-------------|
| `smart_greenhouse_automation.py` | Main application |
| `greenhouse_automation_log.csv` | Full automation event log |
| `greenhouse_session_report.png` | Sensor history chart (auto-saved) |

### Sample CSV Log
```
timestamp,actuator,new_state,trigger_sensor,sensor_value
10:05:02,Fan,ON  ─ Cooling,temperature,34.1
10:05:02,Irrigation,ON  ─ Watering,soil_moisture,28
10:05:04,Fan,OFF ─ Idle,temperature,27.8
...
```

---

## Configuration

```python
POLL_INTERVAL   = 2     # seconds between sensor reads
RUNTIME_SECONDS = 90    # total simulation duration
MAX_HISTORY     = 40    # data points kept for final chart
```

---

##  Key IoT Concepts Demonstrated

- **Conditional automation logic** — 10 sensor-condition → actuator-action rules
- **State-based control** — actuators only change on actual state transitions
- **Multi-sensor fusion** — independent rules for 4 sensor types and 5 actuators
- **Data logging** — every automation event stored in CSV with timestamp
- **Real-time monitoring** — live console output per sensor cycle
- **Session reporting** — end-of-run chart visualizing full sensor history

---

##  Author

**[Fatma Abdelbadie]**  
DecodeLabs IoT Internship — 2026  
GitHub: [fatmaabdebadie]
