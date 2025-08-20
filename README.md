# Canadian Weather Analytics Pipeline — Real-Time ML Alerts

[![Releases](https://img.shields.io/github/v/release/Kirito12o/canadian-weather-analytics-pipeline?label=Releases&style=for-the-badge)](https://github.com/Kirito12o/canadian-weather-analytics-pipeline/releases)

![Weather Stream](https://images.unsplash.com/photo-1501785888041-af3ef285b470?ixlib=rb-1.2.1&auto=format&fit=crop&w=1650&q=80)

Real-time pipeline for ingesting Canadian weather telemetry, running ML-based anomaly detection, and publishing alerts. The stack is serverless on AWS and built for continuous streaming, low cost, and rapid response to anomalous weather events.

Quick links
- Releases: https://github.com/Kirito12o/canadian-weather-analytics-pipeline/releases
  - Download the release file and execute the included deploy script (for example, run the provided ./deploy.sh). The release page hosts packaged artifacts and deploy helpers.
- Topics: aws, aws-free-tier, cloudwatch, data-pipeline, dynamodb, event-driven, iot, kinesis, lambda-functions, real-time-data, serverless, sns, stream-processing, weather-data

Table of contents
- Overview
- Key features
- Architecture diagram
- Components
- Getting started
- Deploy from releases
- Local development and testing
- Data schema and sample events
- ML anomaly detector
- Monitoring and logging
- Cost and scaling
- Security
- CI / CD
- Contributing
- License
- Contact

Overview
This repo contains infrastructure-as-code, Lambda function code, ML model artifacts, and utilities for a real-time Canadian weather analytics pipeline. The pipeline collects sensor data, streams it through Kinesis, enriches and stores core metrics in DynamoDB, runs a lightweight ML model for anomaly detection, and pushes alerts via SNS and CloudWatch metrics.

Key features
- Event-driven design built on AWS serverless services.
- Real-time stream processing using Kinesis Data Streams and Lambda.
- ML-based anomaly detection for temperature, wind, and pressure.
- Edge-friendly ingest via AWS IoT Core or REST input.
- Persistent state and historical reads with DynamoDB.
- Alerting via SNS topics and CloudWatch Alarms.
- Cost-aware defaults tuned for AWS Free Tier and low-volume testing.
- IaC using CloudFormation / SAM for repeatable deploys.

Architecture diagram
![Architecture](https://raw.githubusercontent.com/Kirito12o/canadian-weather-analytics-pipeline/main/docs/architecture.png)

High-level flow
1. Devices or simulators send telemetry to AWS IoT / Kinesis Firehose.
2. Kinesis Data Stream collects records.
3. Lambda consumer batches records, validates schema, and enriches with geodata.
4. The stream processor writes recent metrics to DynamoDB for quick lookups.
5. The processor forwards normalized data to the ML anomaly detector Lambda.
6. The detector returns a score and labels. If anomalous, the pipeline publishes an SNS alert and emits a CloudWatch metric.
7. Downstream subscribers, dashboards, or incident workflows receive alerts.

Components
- infra/ — CloudFormation / SAM templates for network, Kinesis, IAM, DynamoDB, Lambda, SNS.
- src/ingest/ — Lambda for raw ingest, validation, enrichment.
- src/processor/ — Stream processor Lambda for transformation and state writes.
- src/anomaly/ — ML model wrapper and inference Lambda.
- src/simulator/ — Local simulator to generate synthetic Canadian weather telemetry.
- models/ — Pretrained lightweight model artifacts (TensorFlow Lite / ONNX).
- tools/ — Deployment helpers, scripts for packaging artifacts.
- docs/ — Architecture images, schema docs, runbooks.

Getting started — prerequisites
- AWS account and CLI configured.
- Node.js 16+ or Python 3.9+ depending on selected Lambda runtimes.
- SAM CLI for local invocation and packaging (optional).
- Docker (for local containerized Lambda testing).
- IAM user with permissions to create the services in the template.

Deploy from releases
Use the Releases page to get a packaged artifact and deploy script. Visit the Releases page at:
https://github.com/Kirito12o/canadian-weather-analytics-pipeline/releases

Download the release asset and run the included deploy script. Example steps (replace asset name and version as needed):
```bash
# download a release asset (example)
curl -L -o cw-pipeline-v1.0.0.tar.gz \
  https://github.com/Kirito12o/canadian-weather-analytics-pipeline/releases/download/v1.0.0/cw-pipeline-v1.0.0.tar.gz

tar xzf cw-pipeline-v1.0.0.tar.gz
cd cw-pipeline-v1.0.0

# run deploy script (deploy.sh will invoke SAM/CloudFormation)
chmod +x ./deploy.sh
./deploy.sh --profile my-aws-profile --region ca-central-1
```
The release includes a deploy helper that packages Lambda code, uploads model artifacts to S3, and runs CloudFormation. The script accepts profile, region, and parameter overrides.

Local development and testing
- Run the simulator to generate sample telemetry:
```bash
cd src/simulator
npm install
node simulator.js --rate 10 --target kinesis://local-endpoint
```
- Use SAM CLI to invoke Lambdas locally with sample events:
```bash
sam local invoke StreamProcessorFunction -e events/sample-kinesis-event.json
```
- Run unit tests and lint:
```bash
npm run test
npm run lint
```

Data schema and sample events
Telemetry record (JSON)
- device_id: string (UUID)
- timestamp: ISO 8601 UTC
- location: { lat: float, lon: float, station_id: string }
- metrics:
  - temperature_c: float
  - wind_kph: float
  - pressure_hpa: float
  - humidity_pct: float
- meta:
  - firmware_version: string
  - battery_volt: float

Sample Kinesis event payload
```json
{
  "device_id": "a1b2c3d4",
  "timestamp": "2025-08-18T12:34:56Z",
  "location": { "lat": 45.4215, "lon": -75.6972, "station_id": "OTT-001" },
  "metrics": { "temperature_c": -5.4, "wind_kph": 22.3, "pressure_hpa": 1012.5, "humidity_pct": 78 },
  "meta": { "firmware_version": "1.1.2", "battery_volt": 3.7 }
}
```

ML anomaly detector
Design
- Model type: lightweight time-series model with windowed features and residual scoring.
- Input: last N measurements for the device and current metric vector.
- Output: anomaly score (0-1) and flagged metrics.
- Runtime: Lambda, using TensorFlow Lite or ONNX runtime to keep cold starts low.

Training
- Use historical data aggregated in S3.
- Feature examples: rolling mean, stddev, seasonal hour/day, relative difference to station baseline.
- Loss: robust reconstruction loss or isolation forest scoring for multivariate inputs.

Inference
- In Lambda, load the TFLite/ONNX model from a small S3 bucket or included layer.
- Normalize input using stored scalers in DynamoDB or S3.
- Calculate score and threshold against per-station adaptive thresholds.
- If anomaly, emit SNS message and raise CloudWatch metric named WeatherAnomaly.Score.

Example inference pseudocode
```python
features = build_windowed_features(device_id, window_size=24)
score = model.predict(features)
if score > threshold:
    publish_alert(device_id, score, features)
    put_metric('WeatherAnomaly.Score', score)
```

Monitoring and logging
- CloudWatch Logs for each Lambda with structured JSON logs.
- CloudWatch Metrics:
  - Ingest.Rate (records/sec)
  - Processing.Latency (ms)
  - Anomalies.Count (count)
  - Detector.CallErrors (count)
- SNS topic: weather-alerts-ca with subscription endpoints for email, SMS, and Lambda.
- Use CloudWatch Alarms to notify on anomalous trend increases or processing failures.

Cost and scaling
- Kinesis Shards scale with ingest rate. Start small (1 shard) for testing.
- Lambda concurrency managed with reserved concurrency or on-demand.
- DynamoDB uses on-demand mode by default for ease of use and predictable scaling.
- Model inference uses low-memory Lambda tiers to reduce cost.
- The default templates include tags and budget alarms to avoid runaway spend.

Security
- IAM least-privilege roles for each Lambda with specific access to streams, S3, and DynamoDB.
- Kinesis and IoT endpoints restricted to allowed principals.
- Encrypted S3 buckets and server-side encryption for DynamoDB (DynamoDB-managed CMKs).
- Secrets stored in AWS Secrets Manager and provided to functions through environment variables or IAM roles.

CI / CD
- GitHub Actions workflow included for:
  - Linting and unit tests on PR.
  - Packaging artifacts and running integration tests (optional).
  - Publishing a release and uploading packaged artifacts.
- Release workflow tags the repository and creates a release with deployable assets.

Testing strategy
- Unit tests for each Lambda handler and helper module.
- Integration tests that spin up SAM locally and send sample Kinesis events.
- Load tests using the simulator to validate scaling behavior and latency under realistic loads.

Observability runbook (high level)
- If Anomalies.Count spikes:
  - Check CloudWatch Logs for Detector errors.
  - Verify DynamoDB write latencies and provisioned throughput.
  - Validate Kinesis iterator age.
- If processing latency rises:
  - Inspect Lambda memory and increase memory to reduce CPU-bound latency.
  - Review Kinesis shard iterator age and scale shards.

Contributing
- Fork the repo and open a pull request.
- Follow the coding style in .editorconfig.
- Add unit tests for new features and bug fixes.
- Use conventional commits for changelog automation.

Releases
- Releases contain packaged SAM templates, Lambda bundles, and model artifacts. Download the release file from:
  https://github.com/Kirito12o/canadian-weather-analytics-pipeline/releases
- Execute the included deploy script to provision the stack. The deploy script verifies artifacts, uploads to S3, and runs CloudFormation/SAM deploy.

Common commands
- Deploy with SAM (manual)
```bash
sam build
sam package --s3-bucket MY_BUCKET --output-template-file packaged.yaml
sam deploy --template-file packaged.yaml --stack-name cw-pipeline --capabilities CAPABILITY_IAM
```
- Tail logs for a function
```bash
sam logs -n StreamProcessorFunction --stack-name cw-pipeline --tail
```

License
This project uses the MIT License. See LICENSE file for full terms.

Contact
- Repo: https://github.com/Kirito12o/canadian-weather-analytics-pipeline
- Open issues for bugs or feature requests
- Use PRs for contributions

Resources and references
- AWS Kinesis Data Streams docs
- AWS Lambda best practices for streams
- DynamoDB design patterns for time-series
- TensorFlow Lite and ONNX runtime for serverless inference

Badges
[![Releases](https://img.shields.io/github/v/release/Kirito12o/canadian-weather-analytics-pipeline?label=Releases&style=flat-square)](https://github.com/Kirito12o/canadian-weather-analytics-pipeline/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Topics](https://img.shields.io/badge/topics-aws%20%7C%20serverless%20%7C%20kinesis-blue.svg?style=flat-square)](https://github.com/Kirito12o/canadian-weather-analytics-pipeline)

Images and icons
- Header photo from Unsplash (weather theme).
- Architecture and flow diagrams live in docs/. Add or update diagrams and push as needed.