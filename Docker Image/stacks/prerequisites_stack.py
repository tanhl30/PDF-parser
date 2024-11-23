from constructs import Construct
from aws_ddk_core import Configurator, BaseStack
from aws_cdk import (
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as  s3,
    aws_s3_notifications as s3n,
    aws_ecr as ecr, 
    Stage,
    Environment,
    Duration,
    RemovalPolicy, CfnOutput
)


class PreRequisitesStack(BaseStack):
    def __init__(self, scope: Construct, id: str, config: Configurator, **kwargs):
        super().__init__(scope, id, **kwargs)

        repository = ecr.Repository(
            self,
            "PdfParserRepository",
            repository_name="pdf_parser_ecr",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        source_bucket = s3.Bucket(
            self,
            "sourcebucket",
            bucket_name=f'lz-rag-documents-{config.get_config_attribute("account")}-{config.get_config_attribute("region")}-{config.get_config_attribute("name")}',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        
        destination_bucket = s3.Bucket(
            self,
            "destinationbucket",
            bucket_name=f'test-destination-rag-documents-{config.get_config_attribute("account")}-{config.get_config_attribute("region")}-{config.get_config_attribute("name")}',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )


        lambda_role = iam.Role(
            self,
            "PDFParserLambdaRole",
            role_name="pdf_parser_lambda_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        CfnOutput(self, "SourceBucketArn", value=source_bucket.bucket_arn, export_name="SourceBucketArn")
        CfnOutput(self, "DestinationBucketArn", value=destination_bucket.bucket_arn, export_name="DestinationBucketArn")
        CfnOutput(self, "LambdaRoleArn", value=lambda_role.role_arn, export_name="PdfParserLambdaRoleArn")
        CfnOutput(self, "EcrRepoArn", value=repository.repository_arn, export_name="PdfParserEcrRepoArn")
        


        source_bucket.grant_read(lambda_role)
        destination_bucket.grant_write(lambda_role)




class PrerequisitesStage(Stage):
    def __init__(self, scope: Construct, id: str, config: Configurator, tags: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        stacks = list()
        ENV_NAME = config.get_config_attribute('name')

        stack_name_identifier = "PreRequisitesStack" # update stack naming here
        stacks.append(
            PreRequisitesStack( #update stack class here
                self,
                id=stack_name_identifier,
                # dont change this stack name, will cause failure with existing resources
                # stack_name=f"{project}{stack_name_identifier}{ENV_NAME.capitalize()}",
                env=Environment(
                    account=config.get_config_attribute("account"),
                    region=config.get_config_attribute("region"),
                ),
                config=config,
            )
        )

        for stack in stacks:
            for tag in tags.keys():
                stack.tags.set_tag(key=tag, value=tags[tag])

            