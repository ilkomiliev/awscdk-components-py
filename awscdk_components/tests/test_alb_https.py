import unittest

from aws_cdk import (
    core,
    aws_s3
)

from awscdk_components.elb.alb_https import (
    AlbHttpsConstruct,
    AlbCfg,
    add_access_denied_fix_response,
    add_favicon_fix_response
)

from awscdk_components.tests.unittest_utils import (
    GenericTestStack,
    get_template
)


class AlbHttpsTest(unittest.TestCase):

    def test_alb_https_with_401_and_favicon_fix_response(self):
        app = core.App()
        stack = GenericTestStack(app, 'test-stack')
        alb_cfg = AlbCfg(
            alb_name='TestALB',
            vpc=stack.vpc,
            subnets=stack.subnets,
            certificate_arns=['arn:aws:acm:us-east-1:023475735288:certificate/ff6967d7-0fdf-4967-bd68-4caffc983447'],
            cidr_ingress_ranges=[],
            icmp_ranges=[]
        )
        alb_construct = AlbHttpsConstruct(stack, 'albhttps', alb_cfg)
        add_access_denied_fix_response('fix401resp', alb_construct.https_listener)
        add_favicon_fix_response('favicon', alb_construct.https_listener)
        template = get_template(app, stack.stack_name)
        self.assertIn('"Type": "AWS::ElasticLoadBalancingV2::LoadBalancer", '
                      '"Properties": {"Name": "TestALB", "Scheme": "internal"',
                      template,
                      'We have ALB Resource in the template')
        self.assertIn('"Type": "application"', template, 'ALB is of type application')
        self.assertIn(
            '{"Type": "AWS::ElasticLoadBalancingV2::Listener", "Properties": {"DefaultActions": [{'
            '"FixedResponseConfig": {"ContentType": "text/html", "MessageBody": "<html><body><h2>Access '
            'Denied!</h2></body><html>", "StatusCode": "401"}, "Type": "fixed-response"}]',
            template,
            'Listener resource with fix response "401 Access Denied" exists'
        )
        self.assertIn(
            '"Port": 443, "Protocol": "HTTPS", "Certificates": [{"CertificateArn": '
            '"arn:aws:acm:us-east-1:023475735288:certificate/ff6967d7-0fdf-4967-bd68-4caffc983447"}]',
            template,
            'Listener is on HTTPS and has the provided certificate'
        )
        self.assertIn(
            '{"Type": "AWS::ElasticLoadBalancingV2::ListenerRule", "Properties": {"Actions": [{"FixedResponseConfig": '
            '{"ContentType": "text/html", "StatusCode": "201"}, "Type": "fixed-response"}], "Conditions": [{"Field": '
            '"path-pattern", "Values": ["/favicon.ico"]}]',
            template,
            'Fixed response rule for favicon.ico is registered'
        )

    def test_alb_https_with_ingress_rules(self):
        app = core.App()
        stack = GenericTestStack(app, 'test-stack')
        alb_cfg = AlbCfg(
            alb_name='TestALB',
            vpc=stack.vpc,
            subnets=stack.subnets,
            certificate_arns=['arn:aws:acm:us-east-1:023475735288:certificate/ff6967d7-0fdf-4967-bd68-4caffc983447'],
            cidr_ingress_ranges=['10.1.1.1/24', '10.2.2.2/32'],
            icmp_ranges=[]
        )
        alb_construct = AlbHttpsConstruct(stack, 'albhttps', alb_cfg)
        add_access_denied_fix_response('fix401resp', alb_construct.https_listener)
        template = get_template(app, stack.stack_name)
        self.assertIn(
            '"SecurityGroupEgress": [{"CidrIp": "0.0.0.0/0", "Description": "from 0.0.0.0/0:443", "FromPort": 443, '
            '"IpProtocol": "tcp", "ToPort": 443}], '
            '"SecurityGroupIngress": [{"CidrIp": "10.1.1.1/24", "Description": "from 10.1.1.1/24:443", '
            '"FromPort": 443, "IpProtocol": "tcp", "ToPort": 443}, '
            '{"CidrIp": "10.2.2.2/32", "Description": "from 10.2.2.2/32:443", "FromPort": 443, "IpProtocol": "tcp", '
            '"ToPort": 443}]',
            template,
            'The security group ingress rules are applied'
        )

    def test_icmp_is_enabled(self):
        app = core.App()
        stack = GenericTestStack(app, 'test-stack')
        alb_cfg = AlbCfg(
            alb_name='TestALB',
            vpc=stack.vpc,
            subnets=stack.subnets,
            certificate_arns=['arn:aws:acm:us-east-1:023475735288:certificate/ff6967d7-0fdf-4967-bd68-4caffc983447'],
            cidr_ingress_ranges=['10.1.1.1/24', '10.2.2.2/32'],
            icmp_ranges=['10.0.0.1/24', '10.0.2.0/16']
        )
        alb_construct = AlbHttpsConstruct(stack, 'albhttps', alb_cfg)
        add_access_denied_fix_response('fix401resp', alb_construct.https_listener)
        template = get_template(app, stack.stack_name)
        self.assertIn(
            '"SecurityGroupIngress": [{"CidrIp": "10.1.1.1/24", "Description": "from 10.1.1.1/24:443", "FromPort": 443,'
            ' "IpProtocol": "tcp", "ToPort": 443}, {"CidrIp": "10.2.2.2/32", "Description": "from 10.2.2.2/32:443", '
            '"FromPort": 443, "IpProtocol": "tcp", "ToPort": 443}, '
            '{"CidrIp": "10.0.0.1/24", "Description": "from 10.0.0.1/24:ICMP Type 8", '
            '"FromPort": 8, "IpProtocol": "icmp", "ToPort": -1}, {"CidrIp": "10.0.2.0/16", '
            '"Description": "from 10.0.2.0/16:ICMP Type 8", "FromPort": 8, "IpProtocol": "icmp", "ToPort": -1}]',
            template,
            'ICMP ranges are applied to the SG'
        )

    def test_internet_facing_is_applied(self):
        app = core.App()
        stack = GenericTestStack(app, 'test-stack')
        alb_cfg = AlbCfg(
            alb_name='TestALB',
            vpc=stack.vpc,
            subnets=stack.subnets,
            certificate_arns=['arn:aws:acm:us-east-1:023475735288:certificate/ff6967d7-0fdf-4967-bd68-4caffc983447'],
            cidr_ingress_ranges=['0.0.0.0/0'],
            icmp_ranges=[],
            internet_facing=True
        )
        alb_construct = AlbHttpsConstruct(stack, 'albhttps', alb_cfg)
        add_access_denied_fix_response('fix401resp', alb_construct.https_listener)
        template = get_template(app, stack.stack_name)
        self.assertIn(
            '"Scheme": "internet-facing"',
            template,
            'ALB scheme is internet facing'
        )

    def test_internal_schema_is_applied(self):
        app = core.App()
        stack = GenericTestStack(app, 'test-stack')
        alb_cfg = AlbCfg(
            alb_name='TestALB',
            vpc=stack.vpc,
            subnets=stack.subnets,
            certificate_arns=['arn:aws:acm:us-east-1:023475735288:certificate/ff6967d7-0fdf-4967-bd68-4caffc983447'],
            cidr_ingress_ranges=['10.1.1.1/24', '10.2.2.2/32'],
            icmp_ranges=[],
            internet_facing=False
        )
        alb_construct = AlbHttpsConstruct(stack, 'albhttps', alb_cfg)
        add_access_denied_fix_response('fix401resp', alb_construct.https_listener)
        template = get_template(app, stack.stack_name)
        self.assertIn(
            '"Scheme": "internal"',
            template,
            'ALB scheme is internal'
        )

    def test_logging_is_activated(self):
        app = core.App()
        stack = GenericTestStack(app, 'test-stack', env=core.Environment(account="8373873873", region="eu-central-1"))
        logging_s3_bucket = aws_s3.Bucket(stack, 'alb01-logs')
        alb_cfg = AlbCfg(
            alb_name='TestALB',
            vpc=stack.vpc,
            subnets=stack.subnets,
            certificate_arns=['arn:aws:acm:us-east-1:023475735288:certificate/ff6967d7-0fdf-4967-bd68-4caffc983447'],
            cidr_ingress_ranges=['10.1.1.1/24', '10.2.2.2/32'],
            icmp_ranges=[],
            internet_facing=False,
            logging_s3_bucket=logging_s3_bucket,
            logging_prefix='ALB01AccessLogs'
        )
        alb_construct = AlbHttpsConstruct(stack, 'albhttps', alb_cfg)
        add_access_denied_fix_response('fix401resp', alb_construct.https_listener)
        template = get_template(app, stack.stack_name)
        self.assertIn(
            '{"Type": "AWS::ElasticLoadBalancingV2::LoadBalancer", '
            '"Properties": {"LoadBalancerAttributes": [{"Key": "access_logs.s3.enabled", "Value": "true"}, '
            '{"Key": "access_logs.s3.bucket", "Value": {"Ref": "alb01logs',
            template,
            'ALB has logging attribute for S3 bucket enabled'
        )
        self.assertIn(
            '{"Key": "access_logs.s3.prefix", "Value": "ALB01AccessLogs"}]',
            template,
            'ALB has properly set logging attribute prefix'
        )
        self.assertIn(
            '{"Type": "AWS::S3::Bucket"',
            template,
            'S3 bucket is created'
        )
        self.assertIn(
            '"/ALB01AccessLogs/AWSLogs/8373873873/*"',
            template,
            'The bucket policy containing the correct path is created'
        )
