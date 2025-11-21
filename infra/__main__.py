import pulumi
import pulumi_docker as docker
import pulumi_gcp as gcp
from pulumi_gcp import config as gcp_config

config = pulumi.Config()

region = config.get("region") or "europe-west2"  # London by default
service_name = config.get("serviceName") or "hyperact-mcp"
domain = config.get("domain") or "mcp.hyperact.co.uk"
registry = config.get("registry") or f"gcr.io/{gcp_config.project}"
image_name = config.get("imageName") or service_name
image_tag = config.get("imageTag") or pulumi.get_stack()

image_uri = f"{registry}/{image_name}:{image_tag}"

image = docker.Image(
    "app-image",
    image_name=image_uri,
    build=docker.DockerBuildArgs(
        context="..",
        dockerfile="../Dockerfile",
        platform="linux/amd64",
    ),
    skip_push=False,
)

service = gcp.cloudrunv2.Service(
    "service",
    name=service_name,
    location=region,
    ingress="INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER",
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        containers=[
            gcp.cloudrunv2.ServiceTemplateContainerArgs(
                image=image.repo_digest,
                ports=[gcp.cloudrunv2.ServiceTemplateContainerPortArgs(
                    container_port=8080,
                )],
            )
        ],
    ),
)

invoker = gcp.cloudrunv2.ServiceIamMember(
    "invoker",
    name=service.name,
    location=service.location,
    role="roles/run.invoker",
    member="allUsers",
)

neg = gcp.compute.RegionNetworkEndpointGroup(
    "serverless-neg",
    region=region,
    network_endpoint_type="SERVERLESS",
    cloud_run=gcp.compute.RegionNetworkEndpointGroupCloudRunArgs(
        service=service.name,
    ),
)

backend_service = gcp.compute.BackendService(
    "backend",
    load_balancing_scheme="EXTERNAL_MANAGED",
    protocol="HTTP",
    backends=[gcp.compute.BackendServiceBackendArgs(group=neg.id)],
)

url_map = gcp.compute.URLMap(
    "url-map",
    default_service=backend_service.id,
)

ssl_cert = gcp.compute.ManagedSslCertificate(
    "managed-cert",
    managed=gcp.compute.ManagedSslCertificateManagedArgs(
        domains=[domain],
    ),
)

https_proxy = gcp.compute.TargetHttpsProxy(
    "https-proxy",
    url_map=url_map.id,
    ssl_certificates=[ssl_cert.id],
)

http_proxy = gcp.compute.TargetHttpProxy(
    "http-proxy",
    url_map=url_map.id,
)

lb_ip = gcp.compute.GlobalAddress(
    "lb-ip",
    address_type="EXTERNAL",
    ip_version="IPV4",
)

https_rule = gcp.compute.GlobalForwardingRule(
    "https-forwarding-rule",
    load_balancing_scheme="EXTERNAL_MANAGED",
    ip_address=lb_ip.address,
    port_range="443",
    target=https_proxy.id,
)

http_rule = gcp.compute.GlobalForwardingRule(
    "http-forwarding-rule",
    load_balancing_scheme="EXTERNAL_MANAGED",
    ip_address=lb_ip.address,
    port_range="80",
    target=http_proxy.id,
)

pulumi.export("cloud_run_service", service.uri)
pulumi.export("load_balancer_ip", lb_ip.address)
pulumi.export("domain", pulumi.Output.secret(domain))
pulumi.export("image", image.repo_digest)
pulumi.export(
    "next_steps",
    pulumi.Output.format(
        "Point DNS A record for {0} to {1} and wait for managed cert to become ACTIVE.",
        domain,
        lb_ip.address,
    ),
)
