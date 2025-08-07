"""
weather_anomaly_detector.py

Basic anomaly detection logic for Canadian weather data.
This module is used by the Weather Data Processor Lambda function.
"""

def is_anomalous_temperature(temp_celsius: float) -> bool:
    """
    Flags temperature as anomalous if outside realistic Canadian bounds.
    """
    return temp_celsius < -50 or temp_celsius > 45


def is_anomalous_humidity(humidity_percent: float) -> bool:
    """
    Flags humidity as anomalous if outside typical human-perceivable range.
    """
    return humidity_percent < 0 or humidity_percent > 100


def is_anomalous_wind_speed(wind_kph: float) -> bool:
    """
    Flags wind speed as anomalous if it exceeds typical storm speeds.
    """
    return wind_kph > 150


def compute_severity_score(temp: float, humidity: float, wind: float) -> float:
    """
    Computes a basic severity score based on weighted average of weather conditions.
    """
    temp_score = max(0, abs(temp - 22)) / 22  # normalized distance from room temp
    humidity_score = max(0, abs(humidity - 50)) / 50
    wind_score = wind / 150

    # Weighted severity
    return round((0.5 * temp_score + 0.3 * humidity_score + 0.2 * wind_score), 2)


def detect_anomalies(weather_record: dict) -> dict:
    """
    Applies anomaly detection rules and severity scoring to a single weather record.
    """
    temp = weather_record.get("temperature_c")
    humidity = weather_record.get("humidity_percent")
    wind = weather_record.get("wind_kph")

    anomalies = {
        "temperature_anomaly": is_anomalous_temperature(temp),
        "humidity_anomaly": is_anomalous_humidity(humidity),
        "wind_anomaly": is_anomalous_wind_speed(wind)
    }

    severity_score = compute_severity_score(temp, humidity, wind)

    return {
        "anomalies": anomalies,
        "severity_score": severity_score
    }
