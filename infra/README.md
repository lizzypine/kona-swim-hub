# Lightsail CDK deployment

This CDK app provisions the Lightsail Container Service in `us-west-2`. It does not modify the existing Elastic Beanstalk environment, Neon database, or DNS. The service's current application image and runtime settings are managed through the Lightsail console. Do not run `cdk deploy` until the stack definition has been updated to match the active image, public endpoint, and runtime configuration; otherwise it can replace the console-managed deployment and its settings.

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

## Build, push, and deploy an app image

Make sure Docker Desktop is running and the AWS CLI and Lightsail container plugin (`lightsailctl`) are installed. From the repository root, use the Docker Desktop socket configured on this Mac, build the Linux/amd64 image, and push it to the service's built-in registry:

```sh
export DOCKER_HOST=unix:///Users/elizabethpine/.docker/run/docker.sock

docker compose build web
aws lightsail push-container-image \
  --region us-west-2 \
  --service-name kona-swim-hub \
  --profile eb-cli \
  --label web \
  --image kona-swim-hub:local
```

If the Docker socket changes, update `DOCKER_HOST` to match the socket shown by Docker Desktop. The push command prints the new image reference, for example `:kona-swim-hub.web.3`; use the exact reference it reports. In the Lightsail console, open the `kona-swim-hub` container service, create a deployment, and select that newly pushed image for the `web` container.

Uploading an image does not select it for a deployment. Explicitly replace any prefilled image reference in the deployment form, and check the full reference before saving.

Configure the deployment as follows:

- Expose container port `8000` using `HTTP`.
- Enable the public endpoint for container `web` on port `8000`.
- Set the health-check path to `/healthz/`.
- Set the health-check interval to 30 seconds, timeout to 5 seconds, and success codes to `200-299`. Allowing `200-499` hides rejected probe requests such as HTTP 400.
- The app answers exact `/healthz/` GET/HEAD probes before host validation because load-balancer probes can use IP-based Host headers. Other application paths retain normal host validation.
- Copy the active deployment's environment variables, updating only values that need to change. Keep secrets in the Lightsail console; do not put credentials in source files, CDK context, or committed JSON.

Review the image, environment variables, port, and public endpoint before choosing **Save and deploy**. After deployment, confirm that it is active and test the public URL. Use CDK only after the stack definition has been updated to match the console-managed configuration.

Production email uses the verified Resend sending domain `notifications.konaswimhub.com`. The app defaults to `DEFAULT_FROM_EMAIL=Kona Swim Hub <team@notifications.konaswimhub.com>` and `CONTACT_EMAIL=team@konaswimhub.com`; both can be overridden in the deployment environment. The first address is the outgoing sender; the second is the existing inbox for contact messages and administrative copies. Keep that receiving inbox separate from the sending subdomain. Password resets and registration confirmations use the configured sender.

The existing Lightsail service can be disabled or deleted if you decide not to continue; disabling it does not stop its charge.
