# 🧭 Architecture: Real-time Canadian Weather Analytics Pipeline

This document explains the architecture of the real-time serverless weather analytics pipeline, built using AWS services.

---

## 📌 Objective

To stream, process, detect anomalies, and store real-time weather data from Canadian cities using a fully serverless and scalable architecture.

---

✨ Features
⏱️ Real-time ingestion of Canadian weather data
🧠 ML-based anomaly detection for extreme temperatures
📨 Instant alerts via Amazon SNS
🔁 Stream processing with AWS Kinesis
🗃️ Scalable storage using DynamoDB and S3
📊 Export capabilities for historical analytics
⚙️ Infrastructure as Code (CloudFormation & Terraform)
🧪 Integrated testing and deployment automation

---
🛠️ Technology Stack
AWS Services: Lambda · Kinesis · DynamoDB · SNS · S3 · CloudWatch
Infrastructure: CloudFormation · Terraform
Languages: Python · YAML · HCL

---

## 🏗️ High-Level Architecture

```
+------------------------+
| Canadian Weather API   |
+------------------------+
            |
            v
+------------------------+
| AWS Lambda             | <-- weather-data-ingestion
| (pulls API, sends to)  |
+------------------------+
            |
            v
+------------------------+
| Amazon Kinesis Stream  |
+------------------------+
            |
            v
+------------------------+
| AWS Lambda             | <-- weather-data-processor
| (decodes, enriches,    |
| anomaly detection)     |
+------------------------+
            |
    +-------+-------+
    |               |
    v               v
+-----------+ +--------------+
| DynamoDB  | | Amazon SNS   |
| (store)   | | (send alerts)|
+-----------+ +--------------+
    |
    v
+------------------------+
| AWS Lambda             | <-- weather-data-exporter
| (exports to S3 bucket) |
+------------------------+
            |
            v
+-----------------------------+
|    Amazon S3 (Data Lake)    |
+-----------------------------+
```

---

## ⚙️ Services Used

| Component                | AWS Service        | Purpose                                              |
|--------------------------|--------------------| -----------------------------------------------------|
| Data Ingestion           | Lambda             | Pull weather data from public Canadian APIs         |
| Data Streaming           | Kinesis Data Stream| Real-time event ingestion                           |
| Processing & Detection   | Lambda             | Decode, clean, detect anomalies                     |
| Storage                  | DynamoDB           | Store structured, enriched weather data             |
| Alerts                   | SNS                | Notify severe conditions (e.g., extreme heat)       |
| Export                   | Lambda             | Periodically export records to S3                   |
| Data Lake                | Amazon S3          | Store historical, processed datasets                |
| Monitoring               | CloudWatch         | Log and trace all Lambda activity                   |
| Infrastructure-as-Code   | CloudFormation / Terraform | Manage stack and permissions                |

---

## 🧠 ML Integration

- The `weather_anomaly_detector.py` module is integrated in the **Processor Lambda**
- **Flags:**
  - Extreme temperatures (below -50°C or above 45°C)
  - Abnormal humidity or wind speed
- **Outputs:**
  - `anomalies` boolean flags
  - `severity_score` (weighted risk metric)

---

## 🔐 Compliance & Scalability

- **Serverless**: Auto-scales based on volume of incoming data
- **PIPEDA-ready**: No personal or identifying data processed
- **Cost-efficient**: Uses Free Tier eligible services and small compute resources

---

## 📁 Data Flow Summary

1. Weather API data ingested and pushed to Kinesis
2. Kinesis triggers Processor Lambda:
   - Cleans data
   - Detects anomalies using custom logic
   - Stores to DynamoDB
   - Sends alerts if needed
3. Exporter Lambda writes data to S3 for further analysis or archival

---

🔔 Sample SNS Alert Notifications
The pipeline automatically sends alerts for extreme weather conditions in monitored Canadian cities. Alerts are triggered by ML-based anomaly scoring within the data processor Lambda function.
🔥 Extreme Heat Alert
🔥 EXTREME HEAT ALERT 🔥

City: Halifax, NS
Temperature: 39.3°C
Feels Like: 40.4°C
Humidity: 87%

⚠️ Stay hydrated, avoid outdoor activity, and remain indoors if possible.
❄️ Extreme Cold Alert
❄️ EXTREME COLD ALERT ❄️

City: Edmonton, AB
Temperature: -31.8°C
Feels Like: -37.2°C
Humidity: 68%

⚠️ Avoid prolonged outdoor exposure and dress in warm, layered clothing.

---

## 🧑‍💻 Author

**Syed Absar Burney**  
AWS + Data | MSc in IT Management
www.linkedin.com/in/absar-burney


Project created as part of Solutions Architect portfolio.
---

## 📝 License

This project is licensed under the [MIT License](../LICENSE).
