"""
Canadian Weather Data Ingestion Lambda
=====================================

This Lambda function fetches weather data for major Canadian cities and streams it to Kinesis.
Designed to run every 5 minutes via EventBridge (CloudWatch Events).

Environment Variables Required:
- KINESIS_STREAM_NAME: Name of the target Kinesis stream
- OPENWEATHER_API_KEY: API key for OpenWeather API (optional, will simulate if not provided)

Author: [Your Name]
Created: 2024-08-07
"""

import json
import boto3
import requests
import datetime
import os
import random
from decimal import Decimal

def lambda_handler(event, context):
    """
    Main Lambda handler function
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        dict: Response with status code and processing results
    """
    
    # Initialize AWS services
    kinesis = boto3.client('kinesis')
    stream_name = os.environ.get('KINESIS_STREAM_NAME', 'canadian-weather-stream')
    
    # Canadian cities with coordinates and metadata
    cities = {
        'Toronto': {'lat': 43.6532, 'lon': -79.3832, 'province': 'ON', 'region': 'Central'},
        'Vancouver': {'lat': 49.2827, 'lon': -123.1207, 'province': 'BC', 'region': 'West Coast'},
        'Montreal': {'lat': 45.5017, 'lon': -73.5673, 'province': 'QC', 'region': 'Central'},
        'Calgary': {'lat': 51.0447, 'lon': -114.0719, 'province': 'AB', 'region': 'Prairie'},
        'Ottawa': {'lat': 45.4215, 'lon': -75.6972, 'province': 'ON', 'region': 'Central'},
        'Edmonton': {'lat': 53.5461, 'lon': -113.4938, 'province': 'AB', 'region': 'Prairie'},
        'Winnipeg': {'lat': 49.8951, 'lon': -97.1384, 'province': 'MB', 'region': 'Prairie'},
        'Halifax': {'lat': 44.6488, 'lon': -63.5752, 'province': 'NS', 'region': 'Atlantic'},
        'Quebec City': {'lat': 46.8139, 'lon': -71.2082, 'province': 'QC', 'region': 'Central'},
        'Victoria': {'lat': 48.4284, 'lon': -123.3656, 'province': 'BC', 'region': 'West Coast'}
    }
    
    successful_records = 0
    failed_records = 0
    processed_cities = []
    
    for city, details in cities.items():
        try:
            # Fetch or simulate weather data
            weather_data = get_weather_data(city, details)
            
            # Add enrichment and metadata
            weather_data['ingestion_timestamp'] = datetime.datetime.utcnow().isoformat()
            weather_data['data_version'] = '1.0'
            weather_data['pipeline_stage'] = 'ingestion'
            
            # Detect initial alert conditions
            weather_data['alert_flags'] = detect_initial_alerts(weather_data)
            
            # Send to Kinesis
            response = kinesis.put_record(
                StreamName=stream_name,
                Data=json.dumps(weather_data, default=decimal_default),
                PartitionKey=city.replace(' ', '_')  # Ensure consistent partitioning
            )
            
            successful_records += 1
            processed_cities.append(city)
            
            print(f"✅ Successfully sent data for {city} - ShardId: {response['ShardId']}")
            
        except Exception as e:
            failed_records += 1
            print(f"❌ Error processing {city}: {str(e)}")
    
    # Return comprehensive results
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Weather data ingestion completed',
            'successful_records': successful_records,
            'failed_records': failed_records,
            'processed_cities': processed_cities,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'stream_name': stream_name
        })
    }

def get_weather_data(city, city_details):
    """
    Fetch weather data from API or simulate realistic data
    
    Args:
        city (str): City name
        city_details (dict): City metadata including lat/lon
        
    Returns:
        dict: Weather data record
    """
    
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    
    if api_key and api_key != 'demo_key':
        # Use real OpenWeather API
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': city_details['lat'],
                'lon': city_details['lon'],
                'appid': api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'city': city,
                'province': city_details['province'],
                'region': city_details['region'],
                'latitude': city_details['lat'],
                'longitude': city_details['lon'],
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'temperature_celsius': data['main']['temp'],
                'feels_like_celsius': data['main']['feels_like'],
                'humidity_percent': data['main']['humidity'],
                'pressure_hpa': data['main']['pressure'],
                'wind_speed_kmh': data['wind'].get('speed', 0) * 3.6,  # Convert m/s to km/h
                'wind_direction_degrees': data['wind'].get('deg', 0),
                'weather_condition': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description'],
                'visibility_km': data.get('visibility', 10000) / 1000,
                'cloud_cover_percent': data['clouds']['all'],
                'data_source': 'openweather_api'
            }
            
        except Exception as e:
            print(f"API call failed for {city}, falling back to simulation: {e}")
    
    # Simulate realistic Canadian weather data
    return simulate_weather_data(city, city_details)

def simulate_weather_data(city, city_details):
    """
    Generate realistic simulated weather data for Canadian cities
    
    Args:
        city (str): City name
        city_details (dict): City metadata
        
    Returns:
        dict: Simulated weather data
    """
    
    # Get seasonal temperature adjustments
    base_temp = get_seasonal_temperature(city_details['province'])
    
    # Add regional variations
    regional_adjustment = {
        'West Coast': 5,    # Milder due to ocean
        'Prairie': -3,      # Continental climate
        'Central': 0,       # Baseline
        'Atlantic': 2,      # Maritime influence
        'North': -10        # Arctic influence
    }.get(city_details['region'], 0)
    
    temperature = base_temp + regional_adjustment + random.uniform(-5, 5)
    
    # Correlate other weather parameters
    humidity = generate_correlated_humidity(temperature)
    wind_speed = random.uniform(0, 30)
    pressure = random.uniform(980, 1030)
    
    # Weather conditions based on temperature and humidity
    weather_condition = determine_weather_condition(temperature, humidity, wind_speed)
    
    return {
        'city': city,
        'province': city_details['province'],
        'region': city_details['region'],
        'latitude': city_details['lat'],
        'longitude': city_details['lon'],
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'temperature_celsius': round(temperature, 1),
        'feels_like_celsius': round(temperature + random.uniform(-3, 3), 1),
        'humidity_percent': humidity,
        'pressure_hpa': round(pressure, 1),
        'wind_speed_kmh': round(wind_speed, 1),
        'wind_direction_degrees': random.randint(0, 359),
        'weather_condition': weather_condition['main'],
        'weather_description': weather_condition['description'],
        'visibility_km': round(random.uniform(1, 20), 1),
        'cloud_cover_percent': random.randint(0, 100),
        'data_source': 'simulated'
    }

def get_seasonal_temperature(province):
    """
    Get realistic seasonal temperature for Canadian provinces
    
    Args:
        province (str): Province code
        
    Returns:
        float: Base temperature for the season
    """
    
    month = datetime.datetime.now().month
    
    # Base temperatures by season and region
    seasonal_temps = {
        'winter': {'BC': 2, 'AB': -15, 'SK': -18, 'MB': -20, 'ON': -8, 'QC': -12, 'NB': -8, 'NS': -3, 'PE': -5, 'NL': -5},
        'spring': {'BC': 12, 'AB': 8, 'SK': 6, 'MB': 4, 'ON': 15, 'QC': 10, 'NB': 8, 'NS': 8, 'PE': 6, 'NL': 3},
        'summer': {'BC': 22, 'AB': 22, 'SK': 25, 'MB': 25, 'ON': 26, 'QC': 24, 'NB': 22, 'NS': 20, 'PE': 18, 'NL': 15},
        'fall': {'BC': 10, 'AB': 5, 'SK': 2, 'MB': 0, 'ON': 12, 'QC': 8, 'NB': 10, 'NS': 12, 'PE': 8, 'NL': 8}
    }
    
    # Determine season
    if month in [12, 1, 2]:
        season = 'winter'
    elif month in [3, 4, 5]:
        season = 'spring'
    elif month in [6, 7, 8]:
        season = 'summer'
    else:
        season = 'fall'
    
    return seasonal_temps[season].get(province, 0)

def generate_correlated_humidity(temperature):
    """
    Generate humidity that correlates realistically with temperature
    
    Args:
        temperature (float): Temperature in Celsius
        
    Returns:
        int: Humidity percentage
    """
    
    if temperature < -20:
        return random.randint(60, 90)  # Cold air holds less moisture but feels humid
    elif temperature < 0:
        return random.randint(50, 85)
    elif temperature < 20:
        return random.randint(40, 80)
    else:
        return random.randint(30, 90)  # Hot air can hold more moisture

def determine_weather_condition(temperature, humidity, wind_speed):
    """
    Determine weather condition based on parameters
    
    Args:
        temperature (float): Temperature in Celsius
        humidity (int): Humidity percentage
        wind_speed (float): Wind speed in km/h
        
    Returns:
        dict: Weather condition and description
    """
    
    conditions = [
        {'main': 'Clear', 'description': 'clear sky'},
        {'main': 'Clouds', 'description': 'few clouds'},
        {'main': 'Clouds', 'description': 'scattered clouds'},
        {'main': 'Clouds', 'description': 'broken clouds'},
        {'main': 'Clouds', 'description': 'overcast clouds'}
    ]
    
    # Weather logic based on conditions
    if temperature < -10 and humidity > 80:
        return {'main': 'Snow', 'description': 'light snow'}
    elif temperature < 0 and humidity > 85:
        return {'main': 'Snow', 'description': 'snow'}
    elif temperature > 15 and humidity > 80:
        return {'main': 'Rain', 'description': 'light rain'}
    elif humidity > 90:
        return {'main': 'Mist', 'description': 'mist'}
    elif wind_speed > 20:
        return {'main': 'Clouds', 'description': 'windy'}
    else:
        return random.choice(conditions)

def detect_initial_alerts(weather_data):
    """
    Detect initial alert conditions during ingestion
    
    Args:
        weather_data (dict): Weather data record
        
    Returns:
        list: List of alert flags
    """
    
    alerts = []
    temp = weather_data['temperature_celsius']
    humidity = weather_data['humidity_percent']
    wind_speed = weather_data['wind_speed_kmh']
    condition = weather_data['weather_condition']
    
    # Extreme temperature alerts
    if temp <= -30:
        alerts.append('EXTREME_COLD')
    elif temp <= -20:
        alerts.append('COLD_WARNING')
    elif temp >= 35:
        alerts.append('EXTREME_HEAT')
    elif temp >= 30:
        alerts.append('HEAT_WARNING')
    
    # Wind alerts
    if wind_speed >= 25:
        alerts.append('HIGH_WIND')
    elif wind_speed >= 40:
        alerts.append('EXTREME_WIND')
    
    # Storm conditions
    if condition in ['Snow', 'Rain'] and wind_speed > 15 and humidity > 85:
        alerts.append('STORM_CONDITIONS')
    
    # Blizzard potential
    if condition == 'Snow' and wind_speed > 20 and temp < -15:
        alerts.append('BLIZZARD_RISK')
    
    # Fog conditions
    if condition == 'Mist' and weather_data['visibility_km'] < 1:
        alerts.append('DENSE_FOG')
    
    return alerts

def decimal_default(obj):
    """
    JSON serializer for Decimal objects
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serializable version of object
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# For local testing
if __name__ == "__main__":
    # Test the function locally
    test_event = {}
    test_context = {}
    
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
