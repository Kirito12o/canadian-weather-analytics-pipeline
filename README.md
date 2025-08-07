# 🧭 Architecture: Real-time Canadian Weather Analytics Pipeline

This document outlines the architecture of a real-time, serverless weather analytics pipeline built on AWS services for processing Canadian weather data.

---

## 📌 Objective

Create a scalable, serverless pipeline to stream, process, detect anomalies, and store real-time weather data from Canadian cities with automated alerting for extreme conditions.

---

## ✨ Key Features

- ⏱️ Real-time ingestion of Canadian weather data
- 🧠 ML-based anomaly detection for extreme temperatures
- 📨 Instant alerts via Amazon SNS
- 🔁 Stream processing with AWS Kinesis
- 🗃️ Scalable storage using DynamoDB and S3
- 📊 Export capabilities for historical analytics
- ⚙️ Infrastructure as Code (CloudFormation & Terraform)
- 🧪 Integrated testing and deployment automation

---

## 🛠️ Technology Stack

**AWS Services**: Lambda · Kinesis · DynamoDB · SNS · S3 · CloudWatch  
**Infrastructure**: CloudFormation · Terraform  
**Languages**: Python · YAML · HCL

---

## 🏗️ Architecture Overview

```
┌─────────────────────────┐
│   Canadian Weather API  │
└─────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│      AWS Lambda         │ ◄── weather-data-ingestion
│ (API polling & stream)  │
└─────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│  Amazon Kinesis Stream  │
└─────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│      AWS Lambda         │ ◄── weather-data-processor
│ (processing & ML        │
│  anomaly detection)     │
└─────────────────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
┌─────────┐   ┌─────────────┐
│DynamoDB │   │ Amazon SNS  │
│ (store) │   │  (alerts)   │
└─────────┘   └─────────────┘
    │
    ▼
┌─────────────────────────┐
│      AWS Lambda         │ ◄── weather-data-exporter
│   (S3 export batch)     │
└─────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│   Amazon S3 Data Lake   │
└─────────────────────────┘
```

---

## ⚙️ Component Architecture

| Component | AWS Service | Purpose |
|-----------|-------------|---------|
| **Data Ingestion** | Lambda | Pull weather data from Canadian weather APIs |
| **Data Streaming** | Kinesis Data Stream | Real-time event ingestion and buffering |
| **Processing & ML** | Lambda | Data cleaning, enrichment, and anomaly detection |
| **Primary Storage** | DynamoDB | Store structured, real-time weather records |
| **Alerting** | SNS | Send notifications for extreme weather conditions |
| **Data Export** | Lambda | Batch export historical data to S3 |
| **Data Lake** | S3 | Long-term storage for analytics and archival |
| **Monitoring** | CloudWatch | Logging, metrics, and operational visibility |
| **Infrastructure** | CloudFormation/Terraform | Automated provisioning and configuration |

---

## 🧠 ML Anomaly Detection

The `weather_anomaly_detector.py` module is integrated within the processor Lambda function:

**Detection Criteria:**
- Extreme temperatures (below -50°C or above 45°C)
- Abnormal humidity levels or wind speeds
- Historical deviation patterns

**Output Metrics:**
- `anomaly_detected`: Boolean flag for anomalous conditions
- `severity_score`: Weighted risk assessment (0-100 scale)
- `alert_category`: Classification (heat_extreme, cold_extreme, etc.)

---

## 🔔 Alert System

The pipeline sends automated notifications for severe weather conditions via Amazon SNS.

### 🔥 Extreme Heat Alert
```
🔥 EXTREME HEAT ALERT 🔥

City: Halifax, NS
Temperature: 39.3°C
Feels Like: 40.4°C
Humidity: 87%
Severity Score: 85/100

⚠️ Stay hydrated, avoid outdoor activity, and remain indoors if possible.
```

### ❄️ Extreme Cold Alert
```
❄️ EXTREME COLD ALERT ❄️

City: Edmonton, AB
Temperature: -31.8°C
Feels Like: -37.2°C
Humidity: 68%
Severity Score: 78/100

⚠️ Avoid prolonged outdoor exposure and dress in warm, layered clothing.
```

---

## 📊 Data Flow

1. **Ingestion**: Weather data pulled from Canadian APIs and streamed to Kinesis
2. **Processing**: Kinesis triggers processor Lambda to:
   - Clean and validate incoming data
   - Apply ML-based anomaly detection algorithms
   - Store enriched records in DynamoDB
   - Trigger SNS alerts for severe conditions
3. **Export**: Scheduled Lambda function exports data to S3 for historical analysis
4. **Monitoring**: CloudWatch tracks all pipeline activities and performance metrics

---

## 🔐 Architecture Benefits

- **Serverless**: Auto-scales based on data volume with zero infrastructure management
- **Cost-Effective**: Utilizes AWS Free Tier eligible services and pay-per-use pricing
- **Compliant**: PIPEDA-ready architecture with no personal data processing
- **Resilient**: Built-in fault tolerance and automatic retry mechanisms
- **Observable**: Comprehensive logging and monitoring via CloudWatch

---

## 🧑‍💻 Author

**Syed Absar Burney**  
AWS Solutions Architect | Data Engineering Specialist  
MSc in IT Management  
[LinkedIn](https://www.linkedin.com/in/absar-burney)

*Project developed as part of AWS Solutions Architect portfolio demonstration.*

---

## 📝 License

This project is licensed under the MIT License.
