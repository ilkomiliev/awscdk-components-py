import json
import unittest

from aws_cdk import (
    core,
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
