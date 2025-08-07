#!/bin/bash

set -e

# === CONFIGURATION ===
PROJECT_NAME="absarproject"
DEPLOYMENT_BUCKET="absar-burney-deployments"
STACK_NAME="${PROJECT_NAME}-cloudformation-stack"
TERRAFORM_DIR="infrastructure/terraform"
REGION="us-east-1"
LAMBDA_DIR="lambda-functions"
TMP_ZIP_DIR="build"

echo "===================="
echo "🚀 $PROJECT_NAME Deployer"
echo "===================="
echo ""
echo "Choose deployment method:"
echo "1) CloudFormation"
echo "2) Terraform"
read -p "Enter option (1 or 2): " option

# === PACKAGE LAMBDAS ===
echo ""
echo "📦 Packaging Lambda functions..."

rm -rf $TMP_ZIP_DIR
mkdir -p $TMP_ZIP_DIR

for dir in $(find $LAMBDA_DIR -mindepth 1 -maxdepth 1 -type d); do
  FUNCTION_NAME=$(basename $dir)
  ZIP_FILE="$TMP_ZIP_DIR/${FUNCTION_NAME}.zip"

  echo "→ Zipping $FUNCTION_NAME..."
  (cd "$dir" && zip -r "../../$ZIP_FILE" . > /dev/null)
done

echo ""
echo "☁️ Uploading to S3: $DEPLOYMENT_BUCKET"

for zip_file in $TMP_ZIP_DIR/*.zip; do
  aws s3 cp "$zip_file" "s3://$DEPLOYMENT_BUCKET/" --region $REGION
done

# === DEPLOY ===
if [[ "$option" == "1" ]]; then
  echo ""
  echo "🚀 Deploying using CloudFormation..."

  aws cloudformation deploy \
    --template-file infrastructure/cloudformation/main-stack.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --parameter-overrides \
      DeploymentBucket=$DEPLOYMENT_BUCKET

  echo "✅ CloudFormation stack deployed: $STACK_NAME"

elif [[ "$option" == "2" ]]; then
  echo ""
  echo "🚀 Deploying using Terraform..."

  cd "$TERRAFORM_DIR"
  terraform init
  terraform apply -auto-approve
  cd -

  echo "✅ Terraform stack deployed from $TERRAFORM_DIR"

else
  echo "❌ Invalid option. Exiting."
  exit 1
fi

echo ""
echo "🎉 $PROJECT_NAME deployment complete."
