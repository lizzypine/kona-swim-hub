# Lightsail CDK deployment

This CDK app manages a new Lightsail Container Service in `us-west-2`. It does not modify the existing Elastic Beanstalk environment, Neon database, or DNS. The first stack intentionally creates the service without a container deployment so the service's built-in image registry can be used after the service exists.

## Synthesize and review

From this directory, create a Python environment, install the CDK library, then synthesize:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npx --yes aws-cdk@2 synth
```

The synthesized template should contain one `AWS::Lightsail::Container`, with `Power: micro` and `Scale: 1`. Synthesis is local and does not create AWS resources.

## Bootstrap and create the service

Confirm the AWS profile targets the intended account before bootstrapping:

```sh
aws sts get-caller-identity --profile eb-cli
```

CDK bootstrap creates its toolkit resources in the account and region. It is a separate AWS change. After reviewing the account and region, bootstrap and inspect the planned stack change:

```sh
npx --yes aws-cdk@2 bootstrap aws://ACCOUNT_ID/us-west-2 --profile eb-cli
npx --yes aws-cdk@2 diff --profile eb-cli
```

The account was initially bootstrapped with the default `AdministratorAccess` execution policy. Before deploying the service, review [`policies/cdk-execution-policy.json`](policies/cdk-execution-policy.json). It limits the CloudFormation execution role to Lightsail container-service actions in `us-west-2` and read access to this account's CDK bootstrap-version parameter. `Resource: "*"` remains for Lightsail because the service ARN is assigned by AWS at creation; the action family and requested region are restricted. This starter policy does not include certificate/domain actions; add and review those separately before managing the certificate.

After reviewing the policy, create a customer-managed IAM policy and update the CDK bootstrap stack. These commands change AWS IAM/CloudFormation and are intentionally not run by this project setup:

```sh
aws iam create-policy \
  --profile eb-cli \
  --policy-name KonaSwimHubCdkExecution \
  --policy-document file://policies/cdk-execution-policy.json

npx --yes aws-cdk@2 bootstrap aws://971852987284/us-west-2 \
  --profile eb-cli \
  --cloudformation-execution-policies arn:aws:iam::971852987284:policy/KonaSwimHubCdkExecution
```

Then review `cdk diff` again. The `cdk bootstrap` update changes the bootstrap execution role; it does not create the Lightsail service. The deploy profile also needs permission to publish the CDK template artifact and assume the bootstrap roles.

Only after reviewing the diff and approving the Lightsail service cost, create the service:

```sh
npx --yes aws-cdk@2 deploy --profile eb-cli
```

The service is billable even before an image is deployed. The initial resource has no application environment variables or active deployment.

## Push the app image

Build the Linux/amd64 image from the repository root, then push it into the Lightsail service registry:

```sh
cd ..
docker compose build web
aws lightsail push-container-image \
  --region us-west-2 \
  --service-name kona-swim-hub \
  --label web \
  --image kona-swim-hub:local
```

Lightsail prints the registry image reference it created. Use that reference in the next CDK change, which will add the application deployment and runtime environment variables. Do not put Neon credentials or other secrets in source files, CDK context, or committed JSON. The existing Lightsail service can be disabled or deleted if you decide not to continue; disabling it does not stop its charge.

## Certificate and domain

After the deployed app is healthy at the Lightsail default URL, request a Lightsail certificate for `konaswimhub.com` and `www.konaswimhub.com`. Add the exact validation CNAME records from Lightsail to the current DNS provider, wait for the certificate to become valid, then attach it and assign the domains to the service. Change the production traffic records only after testing the custom domains. Keep the old EB environment until the cutover is verified.
