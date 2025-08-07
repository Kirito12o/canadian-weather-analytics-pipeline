"""
Canadian Weather Data Processor Lambda
=====================================

This Lambda function processes weather data from Kinesis stream, performs ML-based analysis,
stores enriched data in DynamoDB, and triggers alerts for severe weather conditions.

Triggered by: Kinesis Data Stream events
Outputs to: DynamoDB, SNS (alerts)

Environment Variables Required:
- DYNAMODB_TABLE: Name of the DynamoDB table for storing weather data
- SNS_TOPIC_ARN: ARN of SNS topic for weather alerts

Author: [Your Name]
Created: 2024-08-07
"""

import json
import boto3
import base64
import os
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Main Lambda handler for processing Kinesis stream events
    
    Args:
        event: Kinesis stream event containing weather data records
        context: Lambda context object
        
    Returns:
        dict: Processing results and statistics
    """
    
    table_name = os.environ.get('DYNAMODB_TABLE', 'CanadianWeatherData')
    table = dynamodb.Table(table_name)
    
    processed_records = 0
    failed_records = 0
    severe_weather_alerts = []
    anomalies_detected = 0
    
    print(f"🔄 Processing {len(event['Records'])} Kinesis records...")
    
    for record in event['Records']:
        try:
            # Decode Kinesis data
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            weather_data = json.loads(payload)
            
            print(f"📍 Processing weather data for {weather_data['city']}")
            
            # Perform ML analysis and enrichment
            processed_data = process_and_enrich_weather_data(weather_data, table)
            
            # Store enhanced data in DynamoDB
            store_weather_data(processed_data, table)
            
            # Advanced pattern analysis
            alerts = perform_advanced_weather_analysis(processed_data, table)
            if alerts:
                severe_weather_alerts.extend(alerts)
            
            # Anomaly detection
            if processed_data.get('anomaly_detected', False):
                anomalies_detected += 1
            
            processed_records += 1
            
        except Exception as e:
            failed_records += 1
            print(f"❌ Error processing record: {str(e)}")
    
    # Send consolidated alerts
    if severe_weather_alerts:
        send_weather_alerts(severe_weather_alerts)
    
    # Log processing summary
    summary = {
        'processed_records': processed_records,
        'failed_records': failed_records,
        'alerts_generated': len(severe_weather_alerts),
        'anomalies_detected': anomalies_detected,
        'processing_timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"📊 Processing Summary: {json.dumps(summary, indent=2)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }

def process_and_enrich_weather_data(weather_data: Dict, table) -> Dict:
    """
    Process and enrich weather data with ML analysis
    
    Args:
        weather_data: Raw weather data from Kinesis
        table: DynamoDB table reference
        
    Returns:
        dict: Enriched weather data with ML features
    """
    
    # Convert floats to Decimal for DynamoDB compatibility
    processed = convert_to_dynamodb_format(weather_data)
    
    # Add processing metadata
    processed['processed_at'] = datetime.utcnow().isoformat()
    processed['pipeline_stage'] = 'processing'
    processed['data_version'] = '2.0'
    
    # Calculate advanced weather metrics
    processed['heat_index'] = calculate_heat_index(
        processed['temperature_celsius'], 
        processed['humidity_percent']
    )
    
    processed['wind_chill'] = calculate_wind_chill(
        processed['temperature_celsius'],
        processed['wind_speed_kmh']
    )
    
    processed['comfort_index'] = calculate_comfort_index(processed)
    
    # Weather severity analysis
    processed['severity_score'] = calculate_advanced_severity_score(processed)
    processed['risk_category'] = categorize_weather_risk(processed['severity_score'])
    
    # Anomaly detection
    processed['anomaly_detected'] = detect_weather_anomalies(processed, table)
    processed['anomaly_score'] = calculate_anomaly_score(processed, table)
    
    # Time-based analysis
    processed['time_of_day'] = get_time_classification()
    processed['season'] = get_season_classification()
    
    # Regional weather analysis
    processed['regional_comparison'] = get_regional_weather_comparison(processed, table)
    
    return processed

def convert_to_dynamodb_format(data: Dict) -> Dict:
    """
    Convert data types for DynamoDB compatibility
    
    Args:
        data: Raw data dictionary
        
    Returns:
        dict: DynamoDB-compatible data
    """
    
    converted = {}
    for key, value in data.items():
        if isinstance(value, float):
            converted[key] = Decimal(str(round(value, 4)))
        elif isinstance(value, int) and not isinstance(value, bool):
            converted[key] = Decimal(str(value))
        else:
            converted[key] = value
    
    return converted

def calculate_heat_index(temperature: Decimal, humidity: Decimal) -> Decimal:
    """
    Calculate heat index (feels-like temperature for hot weather)
    
    Args:
        temperature: Temperature in Celsius
        humidity: Humidity percentage
        
    Returns:
        Decimal: Heat index in Celsius
    """
    
    temp = float(temperature)
    humid = float(humidity)
    
    # Only calculate for temperatures above 20°C
    if temp <= 20:
        return temperature
    
    # Convert to Fahrenheit for calculation
    temp_f = (temp * 9/5) + 32
    
    # Heat index formula (simplified)
    if temp_f >= 80:
        hi = (
            -42.379 +
            2.04901523 * temp_f +
            10.14333127 * humid -
            0.22475541 * temp_f * humid -
            6.83783e-3 * temp_f**2 -
            5.481717e-2 * humid**2 +
            1.22874e-3 * temp_f**2 * humid +
            8.5282e-4 * temp_f * humid**2 -
            1.99e-6 * temp_f**2 * humid**2
        )
        # Convert back to Celsius
        heat_index = (hi - 32) * 5/9
        return Decimal(str(round(heat_index, 1)))
    
    return temperature

def calculate_wind_chill(temperature: Decimal, wind_speed: Decimal) -> Decimal:
    """
    Calculate wind chill temperature
    
    Args:
        temperature: Temperature in Celsius
        wind_speed: Wind speed in km/h
        
    Returns:
        Decimal: Wind chill temperature in Celsius
    """
    
    temp = float(temperature)
    wind = float(wind_speed)
    
    # Only calculate for temperatures below 10°C and wind > 4.8 km/h
    if temp > 10 or wind <= 4.8:
        return temperature
    
    # Wind chill formula for metric units
    wind_chill = (
        13.12 + 0.6215 * temp - 
        11.37 * (wind ** 0.16) + 
        0.3965 * temp * (wind ** 0.16)
    )
    
    return Decimal(str(round(wind_chill, 1)))

def calculate_comfort_index(weather_data: Dict) -> Decimal:
    """
    Calculate overall comfort index (0-10, 10 being most comfortable)
    
    Args:
        weather_data: Weather data dictionary
        
    Returns:
        Decimal: Comfort index score
    """
    
    temp = float(weather_data['temperature_celsius'])
    humidity = float(weather_data['humidity_percent'])
    wind = float(weather_data['wind_speed_kmh'])
    
    comfort_score = 10  # Start with perfect score
    
    # Temperature comfort (optimal: 18-24°C)
    if temp < -10 or temp > 35:
        comfort_score -= 4
    elif temp < 5 or temp > 30:
        comfort_score -= 3
    elif temp < 15 or temp > 27:
        comfort_score -= 2
    elif temp < 18 or temp > 24:
        comfort_score -= 1
    
    # Humidity comfort (optimal: 40-60%)
    if humidity > 80 or humidity < 20:
        comfort_score -= 2
    elif humidity > 70 or humidity < 30:
        comfort_score -= 1
    
    # Wind comfort (light breeze preferred)
    if wind > 25:
        comfort_score -= 2
    elif wind > 15:
        comfort_score -= 1
    elif wind < 5:
        comfort_score -= 0.5
    
    return Decimal(str(max(0, round(comfort_score, 1))))

def calculate_advanced_severity_score(weather_data: Dict) -> Decimal:
    """
    Calculate advanced weather severity score with ML features
    
    Args:
        weather_data: Weather data dictionary
        
    Returns:
        Decimal: Severity score (0-10)
    """
    
    temp = float(weather_data['temperature_celsius'])
    humidity = float(weather_data['humidity_percent'])
    wind = float(weather_data['wind_speed_kmh'])
    pressure = float(weather_data.get('pressure_hpa', 1013))
    visibility = float(weather_data.get('visibility_km', 10))
    
    severity = 0
    
    # Temperature extremes (weighted by Canadian standards)
    if temp <= -35:
        severity += 4
    elif temp <= -25:
        severity += 3
    elif temp <= -15:
        severity += 2
    elif temp <= -5:
        severity += 1
    elif temp >= 40:
        severity += 4
    elif temp >= 35:
        severity += 3
    elif temp >= 30:
        severity += 2
    
    # Wind severity
    if wind >= 40:  # Severe wind
        severity += 3
    elif wind >= 25:  # High wind
        severity += 2
    elif wind >= 15:  # Moderate wind
        severity += 1
    
    # Pressure changes (indicating weather systems)
    if pressure < 980 or pressure > 1040:
        severity += 2
    elif pressure < 990 or pressure > 1030:
        severity += 1
    
    # Visibility issues
    if visibility < 1:
        severity += 2
    elif visibility < 5:
        severity += 1
    
    # Combined conditions multipliers
    if temp < -20 and wind > 20:  # Blizzard conditions
        severity += 2
    
    if temp > 30 and humidity > 80:  # Dangerous heat/humidity
        severity += 2
    
    # Alert flags bonus
    alert_count = len(weather_data.get('alert_flags', []))
    severity += alert_count * 0.5
    
    return Decimal(str(min(10, round(severity, 1))))

def categorize_weather_risk(severity_score: Decimal) -> str:
    """
    Categorize weather risk based on severity score
    
    Args:
        severity_score: Calculated severity score
        
    Returns:
        str: Risk category
    """
    
    score = float(severity_score)
    
    if score >= 8:
        return 'EXTREME'
    elif score >= 6:
        return 'HIGH'
    elif score >= 4:
        return 'MODERATE'
    elif score >= 2:
        return 'LOW'
    else:
        return 'MINIMAL'

def detect_weather_anomalies(current_data: Dict, table) -> bool:
    """
    Detect weather anomalies using statistical analysis
    
    Args:
        current_data: Current weather data
        table: DynamoDB table reference
        
    Returns:
        bool: True if anomaly detected
    """
    
    city = current_data['city']
    current_temp = float(current_data['temperature_celsius'])
    
    try:
        # Get historical data for this city (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        response = table.query(
            KeyConditionExpression='city = :city AND #ts > :timestamp',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':city': city,
                ':timestamp': week_ago
            },
            Limit=50
        )
        
        if len(response['Items']) < 10:
            return False  # Not enough historical data
        
        # Extract temperatures
        historical_temps = [float(item['temperature_celsius']) for item in response['Items']]
        
        # Calculate statistical measures
        mean_temp = statistics.mean(historical_temps)
        std_temp = statistics.stdev(historical_temps) if len(historical_temps) > 1 else 1
