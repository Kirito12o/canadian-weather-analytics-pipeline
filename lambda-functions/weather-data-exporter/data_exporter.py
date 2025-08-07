import json
import boto3
import csv
import os
from datetime import datetime, timedelta
from io import StringIO
from decimal import Decimal

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    bucket_name = os.environ['S3_BUCKET']
    
    try:
        # Fetch weather records from the last 24 hours
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        response = table.scan(
            FilterExpression='#ts > :yesterday',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':yesterday': yesterday}
        )
        
        items = response.get('Items', [])
        
        # Paginate through all records
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='#ts > :yesterday',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={':yesterday': yesterday},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        print(f"Found {len(items)} weather records")
        
        if not items:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No data to export'})
            }

        # Generate exports
        create_raw_data_export(items, s3, bucket_name)
        create_city_summary_export(items, s3, bucket_name)
        create_alerts_export(items, s3, bucket_name)
        create_trend_analysis_export(items, s3, bucket_name)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully exported {len(items)} records',
                'exports_created': 4,
                'bucket': bucket_name
            })
        }

    except Exception as e:
        print(f"Error exporting data: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def create_raw_data_export(items, s3, bucket_name):
    """Export raw weather data as CSV"""
    csv_buffer = StringIO()
    
    # Extract all possible fields
    fieldnames = sorted({key for item in items for key in item.keys()})
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    
    for item in items:
        row = {
            k: float(v) if isinstance(v, Decimal) else
               ', '.join(map(str, v)) if isinstance(v, list) else
               v
            for k, v in item.items()
        }
        writer.writerow(row)
    
    key = f"exports/raw-data/weather-data-{get_timestamp()}.csv"
    upload_to_s3(s3, bucket_name, key, csv_buffer.getvalue(), 'text/csv')
    print(f"Uploaded raw data export: {key}")

def create_city_summary_export(items, s3, bucket_name):
    """Generate summary statistics by city"""
    city_stats = {}

    for item in items:
        city = item.get('city', 'Unknown')
        temp = float(item.get('temperature_celsius', 0))
        severity = float(item.get('severity_score', 0))
        
        stats = city_stats.setdefault(city, {
            'city': city,
            'province': item.get('province', ''),
            'region': item.get('region', ''),
            'record_count': 0,
            'avg_temperature': 0,
            'min_temperature': temp,
            'max_temperature': temp,
            'avg_severity': 0,
            'max_severity': severity,
            'alert_count': 0,
            'latest_timestamp': item.get('timestamp', '')
        })
        
        stats['record_count'] += 1
        stats['avg_temperature'] = ((stats['avg_temperature'] * (stats['record_count'] - 1)) + temp) / stats['record_count']
        stats['min_temperature'] = min(stats['min_temperature'], temp)
        stats['max_temperature'] = max(stats['max_temperature'], temp)
        stats['avg_severity'] = ((stats['avg_severity'] * (stats['record_count'] - 1)) + severity) / stats['record_count']
        stats['max_severity'] = max(stats['max_severity'], severity)
        stats['alert_count'] += len(item.get('alert_flags', []))
        
        if item.get('timestamp', '') > stats['latest_timestamp']:
            stats['latest_timestamp'] = item['timestamp']

    # Round averages
    for stats in city_stats.values():
        stats['avg_temperature'] = round(stats['avg_temperature'], 1)
        stats['avg_severity'] = round(stats['avg_severity'], 1)

    # Export to CSV
    fieldnames = ['city', 'province', 'region', 'record_count', 'avg_temperature',
                  'min_temperature', 'max_temperature', 'avg_severity', 'max_severity',
                  'alert_count', 'latest_timestamp']
    
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(city_stats.values())
    
    key = f"exports/city-summary/city-summary-{get_timestamp()}.csv"
    upload_to_s3(s3, bucket_name, key, csv_buffer.getvalue(), 'text/csv')
    print(f"Uploaded city summary: {key}")

def create_alerts_export(items, s3, bucket_name):
    """Export all weather alerts"""
    alerts = []

    for item in items:
        for alert in item.get('alert_flags', []):
            alerts.append({
                'timestamp': item.get('timestamp', ''),
                'city': item.get('city', ''),
                'province': item.get('province', ''),
                'alert_type': alert,
                'temperature': float(item.get('temperature_celsius', 0)),
                'feels_like': float(item.get('feels_like_temp', item.get('temperature_celsius', 0))),
                'humidity': float(item.get('humidity_percent', 0)),
                'wind_speed': float(item.get('wind_speed_kmh', 0)),
                'severity_score': float(item.get('severity_score', 0)),
                'weather_condition': item.get('weather_condition', '')
            })

    if not alerts:
        print("No alerts to export")
        return

    fieldnames = ['timestamp', 'city', 'province', 'alert_type', 'temperature', 'feels_like',
                  'humidity', 'wind_speed', 'severity_score', 'weather_condition']
    
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(alerts)
    
    key = f"exports/alerts/weather-alerts-{get_timestamp()}.csv"
    upload_to_s3(s3, bucket_name, key, csv_buffer.getvalue(), 'text/csv')
    print(f"Uploaded alerts export: {key} ({len(alerts)} alerts)")

def create_trend_analysis_export(items, s3, bucket_name):
    """Export weather trend data with 3-point moving average"""
    sorted_items = sorted(items, key=lambda x: x.get('timestamp', ''))
    trend_data = []
    city_temps = {}

    for item in sorted_items:
        city = item.get('city', '')
        temp = float(item.get('temperature_celsius', 0))
        city_temps.setdefault(city, []).append(temp)
        
        temp_list = city_temps[city]
        avg_3pt = round(sum(temp_list[-3:]) / min(3, len(temp_list)), 1)
        
        trend_data.append({
            'timestamp': item.get('timestamp', ''),
            'city': city,
            'province': item.get('province', ''),
            'region': item.get('region', ''),
            'temperature': temp,
            'temp_trend_3pt': avg_3pt,
            'feels_like': float(item.get('feels_like_temp', temp)),
            'humidity': float(item.get('humidity_percent', 0)),
            'pressure': float(item.get('pressure_hpa', 1013)),
            'wind_speed': float(item.get('wind_speed_kmh', 0)),
            'severity_score': float(item.get('severity_score', 0)),
            'weather_condition': item.get('weather_condition', ''),
            'alert_count': len(item.get('alert_flags', []))
        })

    fieldnames = ['timestamp', 'city', 'province', 'region', 'temperature', 'temp_trend_3pt',
                  'feels_like', 'humidity', 'pressure', 'wind_speed', 'severity_score',
                  'weather_condition', 'alert_count']
    
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(trend_data)
    
    key = f"exports/trends/trend-analysis-{get_timestamp()}.csv"
    upload_to_s3(s3, bucket_name, key, csv_buffer.getvalue(), 'text/csv')
    print(f"Uploaded trend analysis: {key}")

def upload_to_s3(s3_client, bucket, key, content, content_type='text/csv'):
    """Helper to upload file to S3"""
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=content,
        ContentType=content_type
    )

def get_timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d-%H-%M')
