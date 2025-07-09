#!/usr/bin/env python3
"""
Meshtastic Weather Bot

Fetches weather data from wttr.in and sends it via Meshtastic radio.
Usage: python weather_bot.py [location] [--port /dev/ttyACM0] [--channel 0]
"""

import requests
import meshtastic
import meshtastic.serial_interface
import time
import json
import sys
import argparse
import logging
from typing import Optional, List, Dict, Any

# --- Configuration ---
DEFAULT_SERIAL_PORT = '/dev/ttyACM0'
DEFAULT_WEATHER_LOCATION = '37397'
DEFAULT_CHANNEL = 0
MAX_MESSAGE_LENGTH = 200
REQUEST_TIMEOUT = 10
MESSAGE_DELAY = 7  # seconds between messages

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherBot:
    def __init__(self, serial_port: str = DEFAULT_SERIAL_PORT, 
                 channel: int = DEFAULT_CHANNEL, concise: bool = False):
        self.serial_port = serial_port
        self.channel = channel
        self.concise = concise
        self.interface = None

    def get_weather(self, location: str) -> Optional[Dict[Any, Any]]:
        """Fetches weather data from wttr.in in JSON format."""
        try:
            url = f"https://wttr.in/{location}"
            params = {'format': 'j1'}
            
            logger.info(f"Fetching weather from: {url}")
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            logger.info("Weather data retrieved successfully")
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {REQUEST_TIMEOUT} seconds")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error - check your internet connection")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from weather service")
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
        
        return None

    def format_weather_messages(self, weather_data: Dict[Any, Any]) -> List[str]:
        """Formats weather data into concise strings for Meshtastic."""
        if not weather_data or 'current_condition' not in weather_data:
            return ["Weather data unavailable"]

        try:
            current = weather_data['current_condition'][0]
            
            # Get location info safely
            location_info = self._extract_location_info(weather_data)
            weather_info = self._extract_weather_info(current)
            
            if self.concise:
                return self._create_concise_message(location_info, weather_info)
            else:
                astronomy_info = self._extract_astronomy_info(weather_data)
                
                # Create primary weather message
                message1 = self._create_primary_message(location_info, weather_info)
                
                # Create secondary message with additional info
                message2 = self._create_secondary_message(weather_info, astronomy_info)
                
                # Combine or split messages based on length
                return self._optimize_message_length(message1, message2)
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing weather data: {e}")
            return ["Error parsing weather data"]

    def _extract_location_info(self, weather_data: Dict[Any, Any]) -> Dict[str, str]:
        """Extract location information from weather data."""
        location_info = {
            'area': 'Unknown Location',
            'region': ''
        }
        
        if ('nearest_area' in weather_data and 
            len(weather_data['nearest_area']) > 0):
            nearest = weather_data['nearest_area'][0]
            
            if ('areaName' in nearest and 
                len(nearest['areaName']) > 0):
                location_info['area'] = nearest['areaName'][0]['value']
            
            if ('region' in nearest and 
                len(nearest['region']) > 0):
                location_info['region'] = nearest['region'][0]['value']
        
        return location_info

    def _extract_weather_info(self, current: Dict[Any, Any]) -> Dict[str, str]:
        """Extract weather information from current conditions."""
        weather_desc = 'N/A'
        if ('weatherDesc' in current and 
            len(current['weatherDesc']) > 0):
            weather_desc = current['weatherDesc'][0]['value']
        
        return {
            'temp_c': current.get('temp_C', 'N/A'),
            'temp_f': current.get('temp_F', 'N/A'),
            'feels_like_c': current.get('FeelsLikeC', 'N/A'),
            'feels_like_f': current.get('FeelsLikeF', 'N/A'),
            'description': weather_desc,
            'humidity': current.get('humidity', 'N/A'),
            'wind_speed': current.get('windspeedKmph', 'N/A'),
            'wind_dir': current.get('winddir16Point', 'N/A'),
            'obs_time': current.get('observation_time', 'N/A'),
            'local_time': current.get('localObsDateTime', 'N/A')
        }

    def _extract_astronomy_info(self, weather_data: Dict[Any, Any]) -> Dict[str, str]:
        """Extract sunrise/sunset information."""
        astronomy_info = {
            'sunrise': 'N/A',
            'sunset': 'N/A'
        }
        
        if ('weather' in weather_data and 
            len(weather_data['weather']) > 0 and 
            'astronomy' in weather_data['weather'][0] and 
            len(weather_data['weather'][0]['astronomy']) > 0):
            astronomy_data = weather_data['weather'][0]['astronomy'][0]
            astronomy_info['sunrise'] = astronomy_data.get('sunrise', 'N/A')
            astronomy_info['sunset'] = astronomy_data.get('sunset', 'N/A')
        
        return astronomy_info

    def _create_primary_message(self, location_info: Dict[str, str], 
                              weather_info: Dict[str, str]) -> str:
        """Create the primary weather message."""
        location_str = location_info['area']
        if location_info['region']:
            location_str += f", {location_info['region']}"
        
        return f"""Weather in {location_str}:
Time: {weather_info['local_time']}
Temp: {weather_info['temp_c']}°C ({weather_info['temp_f']}°F)
RealFeel: {weather_info['feels_like_c']}°C ({weather_info['feels_like_f']}°F)
Conditions: {weather_info['description']}
Humidity: {weather_info['humidity']}%"""

    def _create_secondary_message(self, weather_info: Dict[str, str], 
                                astronomy_info: Dict[str, str]) -> str:
        """Create the secondary weather message."""
        return f"""Wind: {weather_info['wind_speed']}km/h {weather_info['wind_dir']}
Sunrise: {astronomy_info['sunrise']}
Sunset: {astronomy_info['sunset']}
Last Obs UTC: {weather_info['obs_time']}"""

    def _create_concise_message(self, location_info: Dict[str, str], 
                              weather_info: Dict[str, str]) -> List[str]:
        """Create a concise natural language weather message."""
        location_str = location_info['area']
        if location_info['region']:
            location_str += f", {location_info['region']}"
        
        # Clean up condition text
        condition = weather_info['description'].lower()
        
        # Build natural language message
        message = f"Weather in {location_str} is {condition} today"
        
        # Add temperature
        if weather_info['temp_c'] != 'N/A':
            message += f" with {weather_info['temp_c']}°C"
            if weather_info['feels_like_c'] != 'N/A' and weather_info['feels_like_c'] != weather_info['temp_c']:
                message += f" (feels like {weather_info['feels_like_c']}°C)"
        
        # Add wind info
        if weather_info['wind_speed'] != 'N/A' and weather_info['wind_speed'] != '0':
            wind_dir = weather_info['wind_dir'] if weather_info['wind_dir'] != 'N/A' else ''
            message += f" and winds at {weather_info['wind_speed']}km/h {wind_dir}".rstrip()
        
        # Add humidity if significant
        if weather_info['humidity'] != 'N/A':
            try:
                humidity_val = int(weather_info['humidity'])
                if humidity_val >= 70:
                    message += f". Humidity {humidity_val}%"
            except ValueError:
                pass
        
        return [message]

    def _optimize_message_length(self, message1: str, message2: str) -> List[str]:
        """Optimize message length for Meshtastic transmission."""
        full_message = message1 + "\n" + message2
        
        if len(full_message) <= MAX_MESSAGE_LENGTH:
            return [full_message]
        else:
            messages = [message1]
            if len(message2.strip()) > 0:
                messages.append(message2)
            return messages

    def connect_meshtastic(self) -> bool:
        """Connect to Meshtastic device."""
        try:
            logger.info(f"Connecting to Meshtastic device on {self.serial_port}")
            self.interface = meshtastic.serial_interface.SerialInterface(self.serial_port)
            time.sleep(1)  # Allow interface to initialize
            logger.info("Connected to Meshtastic device")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Meshtastic device: {e}")
            return False

    def disconnect_meshtastic(self):
        """Disconnect from Meshtastic device."""
        if self.interface:
            try:
                self.interface.close()
                logger.info("Disconnected from Meshtastic device")
            except Exception as e:
                logger.error(f"Error disconnecting from Meshtastic: {e}")
            finally:
                self.interface = None

    def send_message(self, message: str) -> bool:
        """Send a single message via Meshtastic."""
        if not self.interface:
            logger.error("Meshtastic interface not connected")
            return False
        
        try:
            self.interface.sendText(message, channelIndex=self.channel)
            logger.info(f"Message sent to channel {self.channel}")
            logger.info(f"Message content ({len(message)} chars): {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def send_weather_messages(self, messages: List[str]) -> bool:
        """Send multiple weather messages with appropriate delays."""
        if not self.connect_meshtastic():
            return False
        
        try:
            logger.info(f"Sending {len(messages)} weather message(s)")
            
            for i, message in enumerate(messages):
                if not self.send_message(message):
                    logger.error(f"Failed to send message {i+1}, aborting")
                    return False
                
                # Add delay between messages if sending multiple
                if i < len(messages) - 1:
                    logger.info(f"Waiting {MESSAGE_DELAY} seconds before next message...")
                    time.sleep(MESSAGE_DELAY)
            
            logger.info("All weather messages sent successfully")
            return True
            
        finally:
            self.disconnect_meshtastic()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Send weather information via Meshtastic radio'
    )
    
    parser.add_argument(
        'location', 
        nargs='?', 
        default=DEFAULT_WEATHER_LOCATION,
        help=f'Weather location (default: {DEFAULT_WEATHER_LOCATION})'
    )
    
    parser.add_argument(
        '--port', 
        default=DEFAULT_SERIAL_PORT,
        help=f'Serial port for Meshtastic device (default: {DEFAULT_SERIAL_PORT})'
    )
    
    parser.add_argument(
        '--channel', 
        type=int, 
        default=DEFAULT_CHANNEL,
        help=f'Meshtastic channel index (default: {DEFAULT_CHANNEL})'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Fetch and display weather without sending to Meshtastic'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--concise', '-c',
        action='store_true',
        help='Send concise natural language weather summary'
    )
    
    return parser.parse_args()

def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create weather bot instance
    weather_bot = WeatherBot(
        serial_port=args.port,
        channel=args.channel
    )
    
    # Fetch weather data
    logger.info(f"Fetching weather for: {args.location}")
    weather_data = weather_bot.get_weather(args.location)
    
    if not weather_data:
        logger.error("Failed to retrieve weather data")
        return 1
    
    # Format weather messages
    weather_messages = weather_bot.format_weather_messages(weather_data)
    
    # Display messages
    logger.info(f"Generated {len(weather_messages)} weather message(s)")
    for i, msg in enumerate(weather_messages, 1):
        print(f"\n--- Weather Message {i} ({len(msg)} chars) ---")
        print(msg)
        print("-" * 50)
    
    # Send messages (unless dry run)
    if args.dry_run:
        logger.info("Dry run mode - not sending to Meshtastic")
        return 0
    
    if weather_bot.send_weather_messages(weather_messages):
        logger.info("Weather transmission completed successfully")
        return 0
    else:
        logger.error("Weather transmission failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
