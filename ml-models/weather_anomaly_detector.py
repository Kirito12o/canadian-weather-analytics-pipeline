"""
weather_anomaly_detector.py
Enhanced anomaly detection logic for Canadian weather data.
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

def classify_alert_category(temp: float, humidity: float, wind: float, anomalies: dict) -> str:
    """
    Classifies the type of weather alert based on anomalous conditions.
    Returns alert category as specified in README.
    """
    if anomalies.get("temperature_anomaly"):
        if temp < -50 or temp < -30:
            return "cold_extreme"
        elif temp > 45 or temp > 35:
            return "heat_extreme"
    
    if anomalies.get("wind_anomaly"):
        if wind > 100:
            return "wind_extreme"
    
    if anomalies.get("humidity_anomaly"):
        return "humidity_extreme"
    
    # If multiple anomalies or general severe conditions
    if sum(anomalies.values()) > 1:
        return "severe_weather"
    
    return "moderate_alert"

def compute_severity_score(temp: float, humidity: float, wind: float) -> int:
    """
    Computes severity score scaled to 0-100 range as specified in README.
    Higher scores indicate more dangerous conditions.
    """
    # Temperature scoring (0-40 points)
    if temp < -40:
        temp_score = 40
    elif temp < -30:
        temp_score = 30
    elif temp < -20:
        temp_score = 15
    elif temp > 40:
        temp_score = 35
    elif temp > 35:
        temp_score = 25
    elif temp > 30:
        temp_score = 15
    else:
        # Comfortable range gets minimal score
        temp_score = max(0, abs(temp - 22) / 22 * 10)
    
    # Humidity scoring (0-25 points)
    if humidity < 10 or humidity > 95:
        humidity_score = 25
    elif humidity < 20 or humidity > 85:
        humidity_score = 15
    else:
        humidity_score = max(0, abs(humidity - 50) / 50 * 10)
    
    # Wind scoring (0-35 points)
    if wind > 120:
        wind_score = 35
    elif wind > 100:
        wind_score = 25
    elif wind > 80:
        wind_score = 15
    else:
        wind_score = min(wind / 80 * 10, 10)
    
    # Combine scores and ensure 0-100 range
    total_score = int(temp_score + humidity_score + wind_score)
    return min(max(total_score, 0), 100)

def check_historical_deviation_patterns(weather_record: dict, city: str = None) -> dict:
    """
    Placeholder for historical deviation pattern analysis.
    This is a future enhancement as mentioned in the README.
    
    In a full implementation, this would:
    - Compare current readings against historical averages for the city/season
    - Detect unusual trends or rapid changes
    - Use statistical methods (z-scores, percentiles) for deviation analysis
    """
    # Placeholder implementation - always returns no historical anomalies for now
    # TODO: Implement actual historical comparison logic
    return {
        "historical_temp_deviation": False,
        "historical_humidity_deviation": False,
        "historical_wind_deviation": False,
        "trend_analysis": "not_implemented",
        "seasonal_context": "not_implemented"
    }

def detect_anomalies(weather_record: dict) -> dict:
    """
    Applies anomaly detection rules and severity scoring to a single weather record.
    Returns comprehensive anomaly analysis as specified in README.
    """
    temp = weather_record.get("temperature_c")
    humidity = weather_record.get("humidity_percent")
    wind = weather_record.get("wind_kph")
    city = weather_record.get("city", "Unknown")
    
    # Basic anomaly detection
    anomalies = {
        "temperature_anomaly": is_anomalous_temperature(temp),
        "humidity_anomaly": is_anomalous_humidity(humidity),
        "wind_anomaly": is_anomalous_wind_speed(wind)
    }
    
    # Overall anomaly flag (README requirement: anomaly_detected boolean)
    anomaly_detected = any(anomalies.values())
    
    # Severity scoring (README requirement: 0-100 scale)
    severity_score = compute_severity_score(temp, humidity, wind)
    
    # Alert classification (README requirement: alert_category)
    alert_category = classify_alert_category(temp, humidity, wind, anomalies)
    
    # Historical deviation analysis (README requirement: placeholder)
    historical_patterns = check_historical_deviation_patterns(weather_record, city)
    
    return {
        # Core README requirements
        "anomaly_detected": anomaly_detected,
        "severity_score": severity_score,
        "alert_category": alert_category,
        
        # Detailed anomaly breakdown
        "anomalies": anomalies,
        
        # Historical analysis (future enhancement)
        "historical_patterns": historical_patterns,
        
        # Additional context for debugging/monitoring
        "weather_conditions": {
            "temperature_c": temp,
            "humidity_percent": humidity,
            "wind_kph": wind,
            "city": city
        }
    }

def get_alert_message(detection_result: dict) -> str:
    """
    Generates human-readable alert message based on detection results.
    Used by SNS notification system.
    """
    category = detection_result.get("alert_category")
    conditions = detection_result.get("weather_conditions", {})
    severity = detection_result.get("severity_score", 0)
    
    city = conditions.get("city", "Unknown City")
    temp = conditions.get("temperature_c", 0)
    humidity = conditions.get("humidity_percent", 0)
    wind = conditions.get("wind_kph", 0)
    
    if category == "heat_extreme":
        return f"""🔥 EXTREME HEAT ALERT 🔥

City: {city}
Temperature: {temp}°C
Humidity: {humidity}%
Wind Speed: {wind} km/h
Severity Score: {severity}/100

⚠️ Stay hydrated, avoid outdoor activity, and remain indoors if possible."""
    
    elif category == "cold_extreme":
        return f"""❄️ EXTREME COLD ALERT ❄️

City: {city}
Temperature: {temp}°C
Humidity: {humidity}%
Wind Speed: {wind} km/h
Severity Score: {severity}/100

⚠️ Avoid prolonged outdoor exposure and dress in warm, layered clothing."""
    
    elif category == "wind_extreme":
        return f"""💨 EXTREME WIND ALERT 💨

City: {city}
Wind Speed: {wind} km/h
Temperature: {temp}°C
Severity Score: {severity}/100

⚠️ Avoid travel and secure loose objects. Stay indoors."""
    
    else:
        return f"""⚠️ WEATHER ALERT ⚠️

City: {city}
Temperature: {temp}°C
Humidity: {humidity}%
Wind Speed: {wind} km/h
Severity Score: {severity}/100

⚠️ Monitor conditions and exercise caution."""
