#!/usr/bin/env python3
import os

import aws_cdk as cdk

from kona_swim_hub_stack import KonaSwimHubLightsailStack


app = cdk.App()

KonaSwimHubLightsailStack(
    app,
    "KonaSwimHubLightsail",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("LIGHTSAIL_REGION", "us-west-2"),
    ),
)

app.synth()