
# ingest-rag-documents-general

This project contains the docker image that parse pdf to tables and text, as well as the CICD pipeline setup  

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Prerequisites

You must have the following installed and configured:

* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) and [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
* [Docker](https://docs.docker.com/get-docker/)
* [Python 3](https://www.python.org/downloads/) - This project is written in Python 3.11
* [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)

## Structure

The project is structured as follows:

```bash
.
├── docker
│   ├── src     
|   |   └── pdf_parser.py       # lambda handler that extract pdf
|   |   └── requirements.txt    # required packages for the lambda image
│   └── Dockerfile              # dockerfile for the lambda image
├── stacks
│   ├── configurations.py       # setup configuration with parameters specified in ddk.json 
│   ├── cicd_infra_stack.py     # setup this repo in codecommit and the cicd pipeline
│   └── pdfparser_stack.py      # main: lambda image creation and configuration
│   ├── prerequisites_stack.py  # setup this to create s3 bucket, ecr repo and lambda role
│   └── utils.py
├── tests
│   └── unit                    # TODO setup tests
├── app.py                      # app entry point
├── cdk.json                    # CDK app configuration
├── ddk.json                    # modify this file to include parameters used in resource setup in stacks
├── requirements.txt            # dependencies
└── README.md
```

## Getting Started

Clone the repository and install the required dependencies on a virtualenv. To manually create a virtualenv on MacOS and Linux:

```bash
$ python -m venv .venv
# Linux, MacOS
$ source .venv/bin/activate
# Windows
$ source .venv/Scripts/activate
```
Once the virtualenv is activated, you can install the required dependencies. 

```bash
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code. 
You MUST run this command before pushing your code to the repository, as cdk.context.json
stores parameters used by the synth step of the CICD pipeline. See [here](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html#context-lookups) for more information.

```bash
$ cdk synth
```

## Deploying the CDK app
When running for the first time, deploy the CDK app to setup the repository with the 
CICD pipeline. 

```bash
$ cdk deploy --all --profile <PROFILE_NAME>
```

After deployment or after making changes to your code, commit your changes and push to the 
repository to trigger the CICD pipeline which then deploys the resources you have defined 
in your stacks.

```bash
$ git remote add origin codecommit://<PROFILE_NAME>@<REPOSITORY_NAME>
$ cdk synth # if you have made changes to your code
$ git add .
$ git commit -m "YOUR_COMMIT_MESSAGE"
$ git push origin <BRANCH_NAME>
```

To add additional dependencies, for example other CDK libraries, just add
them to your `requirements.txt` file and rerun the `pip install -r requirements.txt`
command

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


## Notes 
* Everytime the image tag is updated to a new image. The lambda does not automatically update the function, even though the url embeded in the lambda console is linked to the new image. 
See [stackoverflow discussion here](https://stackoverflow.com/questions/75367983/aws-lambda-doesnt-automatically-pick-up-the-latest-image) and [aws cli documentation here](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/update-function-code.html) for more information.

To update the function, you need to manually update the image tag in lambda by doing the following:
```bash
$ aws lambda update-function-code --profile <PROFILE_NAME> --function-name <lambda_name> --image-uri <image-uri:image-tag> 
```

* When new package is used in pdf_parser.py, create and test the image locally before deploying. Check [this link](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions)

1. Open Docker Desktop app
2. run: docker build --platform linux/amd64 -t docker-image:test .
3. run: docker run --platform linux/amd64 -p 9000:8080 docker-image:test
4. In a new terminal windoe, run Invoke-WebRequest -Uri "http://localhost:9000/2015-03-31/functions/function/invocations" -Method Post -Body '{}' -ContentType "application/json"



