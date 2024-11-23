import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    aws_codecommit as codecommit,
    pipelines,
)
from aws_ddk_core import BaseStack
from stacks.configurations import Configs
from stacks.utils import *

from stacks.pdfparser_stack import PdfParserStage
from stacks.prerequisites_stack import PrerequisitesStage

class CicdInfraStack(BaseStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        configs = Configs(self)
        tags = configs.get_config_by_env('cicd').get_config_attribute('tags')
        project = configs.get_config_by_env('cicd').get_config_attribute('project')
        # project_name = tags['ProjectName'] TODO update this in future when recreating from scratch
        project_name = tags['RepositoryName'] # then delete this line
        repository_description = configs.get_config_by_env('cicd').get_config_attribute('repositoryDescription') 
        for tag in tags.keys():
            self.tags.set_tag(key=tag, value=tags[tag])

        codecommit_repo = codecommit.Repository(
            self,
            f"{project}CodecommitRepository",
            repository_name=project_name,
            description=repository_description,
        )

        cicd_artifacts_bucket = get_cicd_artifacts_bucket(self, configs)

        for env_name in [x for x in configs.configs.keys() if x != 'cicd']:
            branch = configs.get_branch_by_env(env_name)

            cicd_pipeline = pipelines.CodePipeline(
                self,
                f'{project}CicdPipeline{env_name.capitalize()}',
                synth=pipelines.ShellStep("Synth",
                    install_commands=[
                        "npm install -g aws-cdk@latest",
                        "pip install -r requirements.txt",
                    ],
                    commands=[
                        "cdk synth",
                    ],
                    input=pipelines.CodePipelineSource.code_commit(
                        repository=codecommit_repo,
                        branch=branch,
                    ),
                ),
                artifact_bucket=cicd_artifacts_bucket,
                cross_account_keys=True,
                pipeline_name=f'{project}Cicd{env_name.capitalize()}',
            )

            # stages updated from self-mutate to deploy the stack to the target account
            stages = list()

            stages.append(
                PrerequisitesStage(
                    self,
                    f"{project}PrerequisitesStage{env_name.capitalize()}",
                    env=cdk.Environment(
                        account=configs.get_config_by_env(env_name).get_config_attribute("account"),
                        region=configs.get_config_by_env(env_name).get_config_attribute("region"),
                    ),
                    config=configs.get_config_by_env(env_name),
                    tags=tags,
                )
            )

            stages.append(
                PdfParserStage(
                    self,
                    f"{project}PdfParserStage{env_name.capitalize()}",
                    env=cdk.Environment(
                        account=configs.get_config_by_env(env_name).get_config_attribute("account"),
                        region=configs.get_config_by_env(env_name).get_config_attribute("region"),
                    ),
                    config=configs.get_config_by_env(env_name),
                    project=project,
                    tags=tags,
                )
            )
            
            for stage in stages:
                cicd_pipeline.add_stage(
                    stage=stage
                )