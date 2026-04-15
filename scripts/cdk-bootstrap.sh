#!/bin/bash
# Run once from Debian machine (where AWS CLI + CDK are configured)
# Usage: ./scripts/cdk-bootstrap.sh <EC2_INSTANCE_ID>
set -euo pipefail

INSTANCE_ID=${1:?"Usage: $0 <EC2_INSTANCE_ID>"}
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "==> Account: $ACCOUNT  Region: $REGION  Instance: $INSTANCE_ID"

cd cdk
pip install -r requirements.txt --quiet

echo "==> Bootstrapping CDK environment"
cdk bootstrap "aws://$ACCOUNT/$REGION"

echo "==> Deploying FfDeployStack"
CDK_ACCOUNT=$ACCOUNT CDK_REGION=$REGION \
cdk deploy FfDeployStack \
    --context ec2InstanceId="$INSTANCE_ID" \
    --outputs-file cdk-outputs.json \
    --require-approval never

echo ""
echo "==> Stack deployed. Outputs:"
cat cdk-outputs.json

PROFILE_ARN=$(python3 -c \
    "import json; d=json.load(open('cdk-outputs.json')); \
     print(d['FfDeployStack']['InstanceProfileArn'])")

echo ""
echo "==> Attaching IAM instance profile to EC2"
aws ec2 associate-iam-instance-profile \
    --instance-id "$INSTANCE_ID" \
    --iam-instance-profile Arn="$PROFILE_ARN"

echo ""
echo "==> Done. EC2 can now access S3 bucket ff-draft-room-data."
echo "    Next: SSH into EC2, clone repo, create .env.production, run deploy.sh"
