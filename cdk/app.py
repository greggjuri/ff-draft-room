#!/usr/bin/env python3
"""CDK app entry point for FF Draft Room infrastructure."""

import os

import aws_cdk as cdk

from ff_deploy_stack import FfDeployStack

app = cdk.App()
FfDeployStack(
    app,
    "FfDeployStack",
    env=cdk.Environment(
        account=os.environ["CDK_ACCOUNT"],
        region=os.environ.get("CDK_REGION", "us-east-1"),
    ),
)
app.synth()
