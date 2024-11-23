#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.cicd_infra_stack import CicdInfraStack
from stacks.configurations import Configs

app = cdk.App()
configs = Configs(app)

tags = configs.get_tags()
project_name = tags['Project']

cicd_infra_stack = CicdInfraStack(
    app,
    f"{project_name}CicdInfraStack",
    env={
        "account": configs.get_config_by_env('cicd').get_config_attribute('account'),
        "region": configs.get_config_by_env('cicd').get_config_attribute('region'),
    },
)

app.synth()