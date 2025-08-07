# 🚀 Deployment Guide: Canadian Weather Analytics Pipeline

This document explains how to deploy the Real-time Canadian Weather Analytics Pipeline using AWS CloudFormation, Terraform, and automation scripts.

---

## 📦 Project Structure Overview

```
infrastructure/
├── cloudformation/
│   └── main-stack.yaml
├── terraform/
│   └── main.tf
scripts/
├── deploy.sh
└── destroy.sh
```

---

## 🔧 Prerequisites

Make sure the following are installed and configured before proceeding:

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- [Terraform](https://developer.hashicorp.com/terraform/downloads)
- [Python 3](https://www.python.org/downloads/)
- AWS IAM user with programmatic access and necessary permissions
- Your AWS credentials configured using:

```bash
aws configure
```

---

## ☁️ Deployment Bucket (S3)

All Lambda functions are zipped and uploaded to:

```
s3://absar-burney-deployments/
```

**Important:** Make sure this S3 bucket exists in the `us-east-1` region before deployment.

---

## 📜 Option 1: Deploy Using CloudFormation

```bash
bash scripts/deploy.sh
```

This script will:
1. Zip your Lambda functions
2. Upload them to the S3 deployment bucket
3. Deploy the infrastructure using AWS CloudFormation via `main-stack.yaml`

---

## 📜 Option 2: Deploy Using Terraform

```bash
cd infrastructure/terraform
terraform init
terraform apply
```

The Terraform configuration (`main.tf`) provisions:
- DynamoDB Table for weather data
- S3 bucket for processed output
- IAM Roles and Policies
- Lambda functions with source code from S3

To destroy the infrastructure:

```bash
terraform destroy
```

---

## 🔥 Destroy Resources (CloudFormation)

If deployed via CloudFormation:

```bash
bash scripts/destroy.sh
```

This deletes the CloudFormation stack and optionally clears deployment artifacts from S3.

---

## ✅ Post-Deployment

Once deployed, the system provides:
- Real-time weather data ingestion via Kinesis Stream
- Lambda functions that process, transform, and export weather records
- Automated alerts via Amazon SNS for anomalous readings
- Structured records stored in DynamoDB
- Final datasets exported to S3 bucket

---

## 📁 Outputs

- **Processed JSON Data:** `s3://absar-burney-weather-output/`
- **CloudWatch Logs:** Available for each Lambda function in AWS Console
- **SNS Topic:** Used for sending alerts on severe weather anomalies

---

## 🧪 Run Local Tests

You can run ML model unit tests locally with:

```bash
python -m unittest tests/test_ml_algorithms.py
```

---

## 👤 Author

**Syed Absar Burney**  
MSc in Management of IT, AWS Certified  
www.linkedin.com/in/absar-burney

---

## 📝 License

This project is licensed under the MIT License.

---

## 🚀 Quick Start

Ready to deploy? Follow these steps:

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd canadian-weather-analytics
   ```

2. **Configure AWS credentials**
   ```bash
   aws configure
   ```

3. **Create deployment bucket** (if not exists)
   ```bash
   aws s3 mb s3://absar-burney-deployments --region us-east-1
   ```

4. **Deploy using CloudFormation**
   ```bash
   bash scripts/deploy.sh
   ```


```
