import json
import base64
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import statistics

import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

# Environment variables
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'CanadianWeatherData')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')


def lambda_handler(event, context):
    records = event.get("Records", [])
    if not records:
        print("No records found.")
        return {"statusCode": 200, "body": "No data to process."}

    table = dynamodb.Table(DYNAMODB_TABLE)
    severe_weather_alerts = []

    for record in records:
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            weather_data = json.loads(payload)

            # Extract core weather info
            city = weather_data.get("city")
            temperature = float(weather_data.get("temperature"))
            humidity = float(weather_data.get("humidity", 0))
            wind_speed = float(weather_data.get("wind_speed", 0))
            timestamp = weather_data.get("timestamp") or datetime.utcnow().isoformat()

            # Calculate derived metrics
            feels_like_temp = calculate_feels_like_temperature(temperature, humidity)
            wind_chill = calculate_wind_chill(temperature, wind_speed)
            comfort_index = (feels_like_temp + wind_chill) / 2

            # Retrieve last 7 days of data
            historical_data = get_last_7_days_data(city, table)
            severity_score = calculate_severity_score(temperature, historical_data)
            risk_level = categorize_risk(severity_score)

            enriched_data = {
                "city": city,
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "feels_like_temp": feels_like_temp,
                "wind_chill": wind_chill,
                "comfort_index": comfort_index,
                "severity_score": severity_score,
                "risk_level": risk_level,
            }

            # Store enriched data in DynamoDB
            table.put_item(Item=json.loads(json.dumps(enriched_data), parse_float=Decimal))

            # Queue severe alerts
            if risk_level in ["HIGH", "EXTREME"]:
                severe_weather_alerts.append(enriched_data)

        except Exception as e:
            print(f"Error processing record: {str(e)}")
            continue

    # Publish severe alerts
    if severe_weather_alerts:
        send_weather_alerts(severe_weather_alerts)

    return {"statusCode": 200, "body": f"Processed {len(records)} records."}


# ---------- Helper Functions ----------

def calculate_feels_like_temperature(temp: float, humidity: float) -> float:
    """Simplified 'feels like' temperature formula"""
    return temp + (0.33 * humidity) - (0.7 * 5) - 4.0


def calculate_wind_chill(temp: float, wind_speed: float) -> float:
    """Wind chill calculation (applies only under 10°C and wind > 4.8 km/h)"""
    if temp <= 10 and wind_speed > 4.8:
        return 13.12 + 0.6215 * temp - 11.37 * wind_speed ** 0.16 + 0.3965 * temp * wind_speed ** 0.16
    return temp


def get_last_7_days_data(city: str, table) -> List[float]:
    """Query DynamoDB for last 7 days of temperature data for anomaly detection"""
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("city").eq(city) &
                                   boto3.dynamodb.conditions.Key("timestamp").between(
                                       seven_days_ago.isoformat(), now.isoformat()
                                   ),
            ProjectionExpression="temperature"
        )
        return [float(item["temperature"]) for item in response.get("Items", [])]
    except ClientError as e:
        print(f"DynamoDB query error: {e}")
        return []


def calculate_severity_score(current_temp: float, historical_temps: List[float]) -> float:
    """Returns a z-score-like anomaly metric"""
    if not historical_temps or len(historical_temps) < 3:
        return 0.0
    mean = statistics.mean(historical_temps)
    stdev = statistics.stdev(historical_temps)
    if stdev == 0:
        return 0.0
    return abs((current_temp - mean) / stdev)


def categorize_risk(score: float) -> str:
    """Categorize severity score into risk levels"""
    if score > 3:
        return "EXTREME"
    elif score > 2:
        return "HIGH"
    elif score > 1:
        return "MODERATE"
    elif score > 0.5:
        return "LOW"
    return "MINIMAL"


def send_weather_alerts(alerts: List[Dict[str, Any]]) -> None:
    """Sends alerts to SNS for severe weather events"""
    if not SNS_TOPIC_ARN:
        print("SNS_TOPIC_ARN not set. Skipping alerts.")
        return

    for alert in alerts:
        try:
            message = (
                f"⚠️ Severe Weather Alert for {alert['city']}:\n"
                f"• Temp: {alert['temperature']}°C\n"
                f"• Humidity: {alert['humidity']}%\n"
                f"• Risk Level: {alert['risk_level']}\n"
                f"• Severity Score: {alert['severity_score']:.2f}\n"
                f"• Timestamp: {alert['timestamp']}"
            )

            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=message,
                Subject=f"Severe Weather Alert - {alert['city']}"
            )
            print(f"Alert sent for {alert['city']}")
        except Exception as e:
            print(f"Error sending alert for {alert.get('city')}: {str(e)}")
