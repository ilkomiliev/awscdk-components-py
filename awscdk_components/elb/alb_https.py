from aws_cdk import (
    core,
    aws_ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_s3
)

from awscdk_components.elb import alb_utils


class AlbCfg:
    """
        Configuration for the ALB construct
    """

    alb_name: str
    vpc: aws_ec2.IVpc
    subnets: aws_ec2.SubnetSelection
    certificate_arns: [str]
    cidr_ingress_ranges: [str]
    icmp_ranges: [str]
    internet_facing: bool
    logging_s3_bucket: aws_s3.IBucket
    logging_prefix: str

    def __init__(
            self,
            alb_name: str,
            vpc: aws_ec2.IVpc,
            subnets: aws_ec2.SubnetSelection,
            certificate_arns: [str],
            cidr_ingress_ranges: [str],
            icmp_ranges: [str],
            internet_facing: bool = False,
            logging_s3_bucket: aws_s3.IBucket = None,
            logging_prefix: str = None
    ) -> None:
        self.alb_name = alb_name
        self.vpc = vpc
        self.subnets = subnets
        self.certificate_arns = certificate_arns
        self.cidr_ingress_ranges = cidr_ingress_ranges
        self.icmp_ranges = icmp_ranges
        self.internet_facing = internet_facing
        self.logging_s3_bucket = logging_s3_bucket
        self.logging_prefix = logging_prefix


class AlbHttpsConstruct(core.Construct):
    """
        Creates ALB with HTTPS listener according to the provided AlbCfg configuration.

        Configures the security group ingress rules according to the provided CIDR ranges. Optionally,
        if there are icmp_ranges provided, opens these for ICMP ping, useful for testing the connectivity.
        Additionally opens the egress to everywhere on port 443 - this is needed to be able to
        communicate with the other AWS services via the AWS endpoints. The created ALB and listener
        are exposed and can be referenced from the outside, see the load_balancer and https_listener
        attributes.
    """

    load_balancer: elbv2.ApplicationLoadBalancer
    https_listener: elbv2.ApplicationListener

    def __init__(
            self,
            scope: core.Construct,
            id1: str,
            alb_config: AlbCfg,
            **kwargs
    ) -> None:
        super().__init__(scope, id1, **kwargs)
        self.alb_config = alb_config

        alb_name = alb_config.alb_name
        vpc = alb_config.vpc
        subnets = alb_config.subnets
        certificate_arns = alb_config.certificate_arns
        internet_facing = alb_config.internet_facing

        self.load_balancer = self.create_alb(alb_name, vpc, subnets, internet_facing)
        self.https_listener = self.create_https_listener(certificate_arns)
        self.configure_cidr_ingress()
        if alb_config.logging_s3_bucket:
            alb_utils.enable_logging(
                load_balancer=self.load_balancer,
                logging_s3_bucket=alb_config.logging_s3_bucket,
                logging_prefix=alb_config.logging_prefix
            )

    def create_alb(
            self,
            alb_name: str,
            vpc: aws_ec2.IVpc,
            subnets: aws_ec2.SubnetSelection,
            internet_facing: bool
    ):
        alb = elbv2.ApplicationLoadBalancer(
            self,
            id=alb_name,
            vpc=vpc,
            load_balancer_name=alb_name,
            vpc_subnets=subnets,
            internet_facing=internet_facing
        )
        return alb

    def create_https_listener(
            self,
            certificate_arns: [str]
    ):
        https_listener = self.load_balancer.add_listener(
            id='httpslstiner',
            certificate_arns=certificate_arns,
            open=False,
            protocol=elbv2.ApplicationProtocol.HTTPS
        )
        https_listener.connections.allow_to_any_ipv4(aws_ec2.Port.tcp(443))
        return https_listener

    def configure_cidr_ingress(self):
        configure_cidr_ingress_rules(
            self.alb_config.cidr_ingress_ranges,
            self.https_listener
        )
        if self.alb_config.icmp_ranges:
            configure_icmp_ping_rules(self.alb_config.icmp_ranges, self.https_listener)


def configure_cidr_ingress_rules(
        cidr_list: [str],
        https_listener: elbv2.ApplicationListener
) -> None:
    """
        Opens the security group ingress of the ALB listener for the provided CIDR ranges
        on the listener's default port.
    """
    for cidr in cidr_list:
        https_listener.connections.allow_default_port_from(aws_ec2.Peer.ipv4(cidr))


def configure_icmp_ping_rules(
        cidr_list: [str],
        alb_listener: elbv2.ApplicationListener
) -> None:
    """
        Allows the ALB listener to be pinged from the defined CIDR ranges.
    """
    for cidr in cidr_list:
        alb_listener.connections.allow_from(aws_ec2.Peer.ipv4(cidr), aws_ec2.Port.icmp_ping())


def add_favicon_fix_response(
        id: str,
        alb_listener: elbv2.ApplicationListener,
        priority: int = 1
) -> None:
    """
        Adds fixed response rule for /favicon.ico in the listener.

        Returns fix 201 status code as text/html content type
    """
    alb_listener.add_fixed_response(
        id=id,
        priority=priority,
        path_pattern='/favicon.ico',
        status_code='201',
        content_type=elbv2.ContentType.TEXT_HTML
    )


def add_access_denied_fix_response(
        id: str,
        alb_listener: elbv2.ApplicationListener
) -> None:
    """
        All unmatched requests will return 401 Access Denied response to the client.
    """
    alb_listener.add_fixed_response(
        id=id,
        status_code='401',
        content_type=elbv2.ContentType.TEXT_HTML,
        message_body='<html><body><h2>Access Denied!</h2></body><html>'
    )


class AlbHttpsStack(core.Stack):

    def __init__(self, scope: core.Construct, id1: str, alb_config: AlbCfg, **kwargs) -> None:
        super().__init__(scope, id1, **kwargs)

        AlbHttpsConstruct(self, id1, alb_config, **kwargs)
