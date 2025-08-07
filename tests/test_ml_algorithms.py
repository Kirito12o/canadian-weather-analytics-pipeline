import unittest
from ml_models.weather_anomaly_detector import is_anomalous

class TestWeatherAnomalyDetection(unittest.TestCase):
    
    def test_normal_weather(self):
        normal_record = {
            "city": "Toronto, ON",
            "temperature": 22,
            "humidity": 60,
            "wind_speed": 10
        }
        result = is_anomalous(normal_record)
        self.assertFalse(result, "Expected normal weather to not be flagged as anomalous")

    def test_extreme_temperature(self):
        hot_record = {
            "city": "Edmonton, AB",
            "temperature": 47,  # assuming 47°C is considered anomalous
            "humidity": 30,
            "wind_speed": 12
        }
        result = is_anomalous(hot_record)
        self.assertTrue(result, "Expected high temperature to be flagged as anomalous")

    def test_low_humidity(self):
        dry_record = {
            "city": "Halifax, NS",
            "temperature": 25,
            "humidity": 5,  # very dry
            "wind_speed": 8
        }
        result = is_anomalous(dry_record)
        self.assertTrue(result, "Expected low humidity to be flagged as anomalous")

    def test_high_wind_speed(self):
        windy_record = {
            "city": "Vancouver, BC",
            "temperature": 20,
            "humidity": 50,
            "wind_speed": 100  # hurricane-level wind
        }
        result = is_anomalous(windy_record)
        self.assertTrue(result, "Expected extreme wind speed to be flagged as anomalous")

if __name__ == "__main__":
    unittest.main()
