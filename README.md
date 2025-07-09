# 🌦️ MeshWttr 📡

This script fetches real-time weather data from [wttr.in](https://wttr.in/) and broadcasts it to a Meshtastic mesh network. Now you can get weather updates even in off-grid locations! 🌲

## ✨ Features

*   **Real-time Weather:** Get current weather conditions for any location.
*   **Meshtastic Integration:** Seamlessly sends weather data to your Meshtastic device.
*   **Customizable Location:** Easily specify your desired location for weather updates.
*   **Command-line Friendly:** Run the script with a simple command and optional arguments.

## 🚀 Getting Started

### 1. Prerequisites

*   A Meshtastic device connected to your computer.
*   Python 3 installed on your system.

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/meshtastic-weather.git
    cd meshtastic-weather
    ```
2.  **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Usage

Run the script from your terminal with your desired location as an argument.

**Example:**

```bash
python meshtastic_weather.py "New York"
```

Or, for a specific zip code:

```bash
python meshtastic_weather.py "90210"
```

If you don't provide a location, the script will use the default location specified in the `meshtastic_weather.py` file.

## 📝 Customization

You can change the default weather location by editing the `WEATHER_LOCATION` variable in the `meshtastic_weather.py` file.

```python
# Your desired location for weather. Use 'auto' for automatic detection,
# or a city name, zip code, or airport code (e.g., '~Dunlap+TN', 'London', '90210', 'KJFK').
WEATHER_LOCATION = '37397'
```

##🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/iaintshootinmis/MeshWttr/issues).

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
