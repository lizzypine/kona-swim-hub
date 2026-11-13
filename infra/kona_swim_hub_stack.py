from aws_cdk import CfnOutput, CfnTag, Stack, aws_lightsail as lightsail
from constructs import Construct


class KonaSwimHubLightsailStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        service = lightsail.CfnContainer(
            self,
            "ContainerService",
            service_name="kona-swim-hub",
            power="micro",
            scale=1,
            tags=[
                CfnTag(key="Application", value="kona-swim-hub"),
                CfnTag(key="ManagedBy", value="CDK"),
            ],
            container_service_deployment=lightsail.CfnContainer.ContainerServiceDeploymentProperty(
                containers=[
                    lightsail.CfnContainer.ContainerProperty(
                        container_name="web",
                        image=":kona-swim-hub.web.2",
                        ports=[
                            lightsail.CfnContainer.PortInfoProperty(
                                port="8000",
                                protocol="HTTP",
                            )
                        ],
                        environment=[
                            lightsail.CfnContainer.EnvironmentVariableProperty(
                                variable="DEBUG",
                                value="False",
                            ),
                            lightsail.CfnContainer.EnvironmentVariableProperty(
                                variable="PORT",
                                value="8000",
                            ),
                            lightsail.CfnContainer.EnvironmentVariableProperty(
                                variable="SECRET_KEY",
                                value="replace-me-with-a-real-secret",
                            ),
                            lightsail.CfnContainer.EnvironmentVariableProperty(
                                variable="ALLOWED_HOSTS",
                                value="kona-swim-hub.7db3kqmv94sma.us-west-2.cs.amazonlightsail.com,localhost,127.0.0.1",
                            ),
                            lightsail.CfnContainer.EnvironmentVariableProperty(
                                variable="CSRF_TRUSTED_ORIGINS",
                                value="https://kona-swim-hub.7db3kqmv94sma.us-west-2.cs.amazonlightsail.com",
                            ),
                            lightsail.CfnContainer.EnvironmentVariableProperty(
                                variable="SECURE_PROXY_SSL_HEADER",
                                value="HTTP_X_FORWARDED_PROTO:https",
                            ),
                            lightsail.CfnContainer.EnvironmentVariableProperty(
                                variable="DATABASE_URL",
                                value="sqlite:////data/db.sqlite3",
                            ),
                        ],
                    )
                ],
                public_endpoint=lightsail.CfnContainer.PublicEndpointProperty(
                    container_name="web",
                    container_port=8000,
                    health_check_config=lightsail.CfnContainer.HealthCheckConfigProperty(
                        healthy_threshold=2,
                        unhealthy_threshold=2,
                        timeout_seconds=5,
                        interval_seconds=30,
                        path="/",
                        success_codes="200-499",
                    ),
                ),
            ),
        )

        CfnOutput(
            self,
            "ContainerServiceUrl",
            value=service.attr_url,
            description="Lightsail container service URL; empty service may return 404 until deployed.",
        )