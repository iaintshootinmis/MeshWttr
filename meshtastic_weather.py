import requests
import meshtastic
import meshtastic.serial_interface
import time
import json
import sys

# --- Configuration ---
# Replace with your Meshtastic device's serial port.
# On Linux, this is often something like '/dev/ttyUSB0' or '/dev/ttyACM0'.
# You can find it by running 'ls /dev/tty*' before and after plugging in your device.
SERIAL_PORT = '/dev/ttyACM0' 

# Your desired location for weather. Use 'auto' for automatic detection,
# or a city name, zip code, or airport code (e.g., '~Dunlap+TN', 'London', '90210', 'KJFK').
WEATHER_LOCATION = '37397'

# --- Fetch Weather Data ---
def get_weather(location):
    """Fetches weather data from wttr.in in JSON format."""
    try:
        url = f"https://wttr.in/{location}?format=j1"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
        return None

# --- Format Weather Message ---
def format_weather_message(weather_data):
    """Formats the weather data into a concise string for Meshtastic."""
    if not weather_data or 'current_condition' not in weather_data:
        return "Could not retrieve weather information."

    current = weather_data['current_condition'][0]
    area_name = weather_data['nearest_area'][0]['areaName'][0]['value'] if 'nearest_area' in weather_data else 'Unknown Location'
    region_name = weather_data['nearest_area'][0]['region'][0]['value'] if 'nearest_area' in weather_data else '' 

    # Safely get sunrise and sunset
    sunrise = 'N/A'
    sunset = 'N/A'
    if 'weather' in weather_data and len(weather_data['weather']) > 0 and 'astronomy' in weather_data['weather'][0] and len(weather_data['weather'][0]['astronomy']) > 0:
        astronomy_data = weather_data['weather'][0]['astronomy'][0]
        sunrise = astronomy_data.get('sunrise', 'N/A')
        sunset = astronomy_data.get('sunset', 'N/A')    
    temp_c = current.get('temp_C', 'N/A')
    temp_f = current.get('temp_F', 'N/A')
    real_c = current.get('FeelsLikeC' , 'N/A')
    real_f = current.get('FeelsLikeF', 'N/A')
    weather_desc = current['weatherDesc'][0]['value']
    humidity = current.get('humidity', 'N/A')
    wind_speed_kmph = current.get('windspeedKmph', 'N/A')
    wind_dir = current.get('winddir16Point', 'N/A')
    obstime = current.get('observation_time', 'N/A') 
    time = current.get('localObsDateTime', 'N/A')
    

    message = f"""Weather in {area_name}, {region_name}: 
Time:{time}
Temp: {temp_c}°C ({temp_f}°F)
RealFeel {real_c}°C ({real_f}°F)
Cond: {weather_desc}
Humidity: {humidity}%
Wind: {wind_speed_kmph}km/h {wind_dir}
Sunrise: {sunrise}
Sunset: {sunset}
Last Observation UTC: {obstime}"""
    return message

def send_meshtastic_message(message, serial_port, channel_index=0):
    """Sends a message via Meshtastic over serial."""
    try:
        interface = meshtastic.serial_interface.SerialInterface(serial_port)
        time.sleep(1) # Add a small delay to allow the interface to initialize
        interface.sendText(message, channelIndex=channel_index)
        print(f"Message sent to Meshtastic on channel {channel_index}: '{message}'")
        interface.close()
    except Exception as e:
        print(f"Error sending Meshtastic message: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Check for command-line argument for weather location
    if len(sys.argv) > 1:
        WEATHER_LOCATION = sys.argv[1]
        print(f"Using weather location from command-line argument: {WEATHER_LOCATION}")
    else:
        print(f"Using default weather location: {WEATHER_LOCATION}")
    
    print(f"Fetching weather for {WEATHER_LOCATION}...")
    weather_data = get_weather(WEATHER_LOCATION)
    
    if weather_data:
        weather_message1, weather_message2 = format_weather_message(weather_data)
        print("\n--- Weather Message 1 ---")
        print(weather_message1)
        print("-----------------------\n")
        
        if weather_message2:
            print("\n--- Weather Message 2 ---")
            print(weather_message2)
            print("-----------------------\n")

        print(f"Attempting to send message to Meshtastic device on {SERIAL_PORT}...")
        send_meshtastic_message(weather_message1, SERIAL_PORT, channel_index=0)
        if weather_message2:
            time.sleep(7) # Add a small delay between sending messages
            send_meshtastic_message(weather_message2, SERIAL_PORT, channel_index=0)
    else:
        print("Failed to retrieve weather data. Aborting Meshtastic message.")
