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

# Maximum message length for Meshtastic (adjust based on your needs)
MAX_MESSAGE_LENGTH = 200

# --- Fetch Weather Data ---
def get_weather(location):
    """Fetches weather data from wttr.in in JSON format."""
    try:
        url = f"https://wttr.in/{location}?format=j1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
        return None

# --- Format Weather Message ---
def format_weather_message(weather_data):
    """Formats the weather data into concise strings for Meshtastic."""
    if not weather_data or 'current_condition' not in weather_data:
        return ["Could not retrieve weather information."]

    current = weather_data['current_condition'][0]
    
    # Get location info safely
    area_name = 'Unknown Location'
    region_name = ''
    if 'nearest_area' in weather_data and len(weather_data['nearest_area']) > 0:
        nearest = weather_data['nearest_area'][0]
        if 'areaName' in nearest and len(nearest['areaName']) > 0:
            area_name = nearest['areaName'][0]['value']
        if 'region' in nearest and len(nearest['region']) > 0:
            region_name = nearest['region'][0]['value']

    # Safely get sunrise and sunset
    sunrise = 'N/A'
    sunset = 'N/A'
    if ('weather' in weather_data and 
        len(weather_data['weather']) > 0 and 
        'astronomy' in weather_data['weather'][0] and 
        len(weather_data['weather'][0]['astronomy']) > 0):
        astronomy_data = weather_data['weather'][0]['astronomy'][0]
        sunrise = astronomy_data.get('sunrise', 'N/A')
        sunset = astronomy_data.get('sunset', 'N/A')
    
    # Extract weather data with safe defaults
    temp_c = current.get('temp_C', 'N/A')
    temp_f = current.get('temp_F', 'N/A')
    real_c = current.get('FeelsLikeC', 'N/A')
    real_f = current.get('FeelsLikeF', 'N/A')
    weather_desc = current['weatherDesc'][0]['value'] if 'weatherDesc' in current and len(current['weatherDesc']) > 0 else 'N/A'
    humidity = current.get('humidity', 'N/A')
    wind_speed_kmph = current.get('windspeedKmph', 'N/A')
    wind_dir = current.get('winddir16Point', 'N/A')
    obstime = current.get('observation_time', 'N/A')
    local_time = current.get('localObsDateTime', 'N/A')

    # Create the primary weather message
    location_str = f"{area_name}, {region_name}" if region_name else area_name
    
    message1 = f"""Weather in {location_str}:
Time: {local_time}
Temp: {temp_c}°C ({temp_f}°F)
RealFeel: {real_c}°C ({real_f}°F)
Conditions: {weather_desc}
Humidity: {humidity}%"""

    # Create secondary message with wind and sun info
    message2 = f"""Wind: {wind_speed_kmph}km/h {wind_dir}
Sunrise: {sunrise}
Sunset: {sunset}
Last Obs UTC: {obstime}"""

    messages = []
    
    # Check if we need to split the message
    full_message = message1 + "\n" + message2
    
    if len(full_message) <= MAX_MESSAGE_LENGTH:
        messages.append(full_message)
    else:
        # Split into two messages if too long
        messages.append(message1)
        if len(message2.strip()) > 0:
            messages.append(message2)
    
    return messages

def send_meshtastic_message(message, serial_port, channel_index=0):
    """Sends a message via Meshtastic over serial."""
    try:
        interface = meshtastic.serial_interface.SerialInterface(serial_port)
        time.sleep(1)  # Add a small delay to allow the interface to initialize
        interface.sendText(message, channelIndex=channel_index)
        print(f"Message sent to Meshtastic on channel {channel_index}:")
        print(f"'{message}'")
        print("-" * 50)
        interface.close()
        return True
    except Exception as e:
        print(f"Error sending Meshtastic message: {e}")
        return False

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
        weather_messages = format_weather_message(weather_data)
        
        print(f"\n--- Generated {len(weather_messages)} weather message(s) ---")
        for i, msg in enumerate(weather_messages, 1):
            print(f"\n--- Weather Message {i} ---")
            print(msg)
            print(f"Length: {len(msg)} characters")
        print("-" * 50)

        print(f"\nAttempting to send message(s) to Meshtastic device on {SERIAL_PORT}...")
        
        for i, message in enumerate(weather_messages):
            success = send_meshtastic_message(message, SERIAL_PORT, channel_index=0)
            if not success:
                print(f"Failed to send message {i+1}, aborting remaining messages.")
                break
            
            # Add delay between messages if sending multiple
            if i < len(weather_messages) - 1:
                print("Waiting 7 seconds before sending next message...")
                time.sleep(7)
        
        print("Weather message transmission complete.")
    else:
        print("Failed to retrieve weather data. Aborting Meshtastic message.")
