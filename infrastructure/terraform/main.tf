terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.3"
}

provider "aws" {
  region = var.aws_region
}

variable "environment" {
  default = "dev"
}

variable "aws_region" {
  default = "ca-central-1"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "weather_data_bucket" {
  bucket = "weather-data-bucket-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_sns_topic" "weather_alerts" {
  name = "weather-alerts-topic-${var.environment}"
}

resource "aws_dynamodb_table" "weather_data" {
  name         = "weather-data-table-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "city"
  range_key    = "timestamp"

  attribute {
    name = "city"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }
}

resource "aws_kinesis_stream" "weather_stream" {
  name        = "weather-stream-${var.environment}"
  shard_count = 1
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "weather-lambda-exec-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "data_ingestion" {
  function_name = "weather-data-ingestion-${var.environment}"
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 30
  memory_size   = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.weather_data.name
      SNS_TOPIC_ARN  = aws_sns_topic.weather_alerts.arn
    }
  }

  s3_bucket = "absar-burney-deployment-bucket"
  s3_key    = "weather-data-ingestion.zip"
}

resource "aws_lambda_function" "data_processor" {
  function_name = "weather-data-processor-${var.environment}"
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 30
  memory_size   = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.weather_data.name
      SNS_TOPIC_ARN  = aws_sns_topic.weather_alerts.arn
    }
  }

  s3_bucket = "absar-burney-deployment-bucket"
  s3_key    = "weather-data-processor.zip"
}

resource "aws_lambda_function" "data_exporter" {
  function_name = "weather-data-exporter-${var.environment}"
  runtime       = "python3.12"
  handler       = "data_exporter.lambda_handler"
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 60
  memory_size   = 256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.weather_data.name
      S3_BUCKET      = aws_s3_bucket.weather_data_bucket.bucket
    }
  }

  s3_bucket = "absar-burney-deployment-bucket"
  s3_key    = "weather-data-exporter.zip"
}
