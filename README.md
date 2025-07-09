# Meshtastic Weather Station

This script fetches weather data from wttr.in and sends it to a Meshtastic device.

## Usage

1.  Install the required Python libraries:
    ```
    pip install -r requirements.txt
    ```
2.  Connect your Meshtastic device to your computer.
3.  Run the script with your desired location:
    ```
    python meshtastic_weather.py "Your Location"
    ```
    If no location is provided, it will default to the location specified in the script.
