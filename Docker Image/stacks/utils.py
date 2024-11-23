from aws_cdk import (
    aws_s3 as s3,
    aws_kms as kms,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
)

def get_existing_datalake_buckets(self, config):
    return {
        "bronze": s3.Bucket.from_bucket_attributes(
            self,
            "BronzeBucket", 
            bucket_arn=f"arn:aws:s3:::bronze-{self.account}-{self.region}-{config.get_config_attribute('name')}"
        ),
        "silver": s3.Bucket.from_bucket_attributes(
            self,
            "SilverBucket",
            bucket_arn=f"arn:aws:s3:::silver-{self.account}-{self.region}-{config.get_config_attribute('name')}"
        ),
        "gold": s3.Bucket.from_bucket_attributes(
            self,
            "GoldBucket", 
            bucket_arn=f"arn:aws:s3:::gold-{self.account}-{self.region}-{config.get_config_attribute('name')}"
        ),
    }

def get_aws_sdk_pandas_layer(self, config):
    aws_sdk_pandas_layer_arn = config.get_config_attribute('AwsSdkPandasLayerArn')
    return _lambda.LayerVersion.from_layer_version_arn(self, 'AWSSDKPandasLayer',
        layer_version_arn=config.get_config_attribute('AwsSdkPandasLayerArn')
    )

def get_kms_data_key(self, config):
    return kms.Key.from_lookup(
        self, 
        "KmsDataKey", 
        #key_arn=config.get_config_attribute('KmsDataKeyArn')
        alias_name=f"alias/dwh-datalake-data-key-{config.get_config_attribute('name')}",
    )

def get_kms_cicd_key(self, configs):
    return kms.Key.from_lookup(
        self,
        "KmsCicdKey",
        alias_name='alias/cdk-codepipelineartifacts-cicd-key',
    )

def get_cicd_artifacts_bucket(self, configs):
    return s3.Bucket.from_bucket_attributes(
        self,
        "CicdArtifactsBucket",
        bucket_name=f"cdk-codepipelineartifacts-{configs.get_config_by_env('cicd').get_config_attribute('account')}-{configs.get_config_by_env('cicd').get_config_attribute('region')}",
        encryption_key=get_kms_cicd_key(self, configs),
    )

def get_vpc(self, config):
    return ec2.Vpc.from_lookup(self, 
        "Vpc", 
        vpc_id=config.get_config_attribute('vpcId'), 
        owner_account_id=config.get_config_attribute("account"),
        region=config.get_config_attribute("region"),
    )