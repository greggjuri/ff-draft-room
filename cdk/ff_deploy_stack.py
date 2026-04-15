"""CDK stack for FF Draft Room — S3 bucket + IAM role + instance profile."""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class FfDeployStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = "ff-draft-room-data"

        # S3 bucket for rankings data
        bucket = s3.Bucket(
            self,
            "RankingsBucket",
            bucket_name=bucket_name,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(90),
                ),
            ],
        )

        # IAM role for EC2 instance
        role = iam.Role(
            self,
            "Ec2Role",
            role_name="ff-draft-room-ec2-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )

        # Grant S3 access scoped to this bucket
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                ],
                resources=[f"{bucket.bucket_arn}/*"],
            )
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[bucket.bucket_arn],
            )
        )

        # Instance profile wrapping the role
        instance_profile = iam.CfnInstanceProfile(
            self,
            "InstanceProfile",
            instance_profile_name="ff-draft-room-instance-profile",
            roles=[role.role_name],
        )

        CfnOutput(self, "BucketName", value=bucket.bucket_name)
        CfnOutput(
            self,
            "InstanceProfileArn",
            value=instance_profile.attr_arn,
        )
