from unittest import TestCase
from aws_cdk import core, aws_ec2

from awscdk_components.elb.alb_https import (
    AlbHttpsConstruct,
    AlbCfg, add_access_denied_fix_response
)
from awscdk_components.elb.alb_utils import register_ec2_as_alb_target

from awscdk_components.tests.unittest_utils import (
    GenericTestStack,
    get_template
)


class AlbUtilsTest(TestCase):

    def test_register_lambda_target_group_with_cognito_auth_rule(self):
        pass

    def test_register_ec2_as_alb_target(self):
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
        ec2 = aws_ec2.Instance(
            scope=stack,
            id='ec2foralb',
            vpc=stack.vpc,
            instance_type=aws_ec2.InstanceType(instance_type_identifier='t3.micro'),
            machine_image=aws_ec2.MachineImage.latest_amazon_linux()
        )
        register_ec2_as_alb_target(
            stack,
            ec2=ec2,
            listener=alb_construct.https_listener,
            vpc=stack.vpc,
            path_pattern_values=['/ec2'],
            port=443
        )
        add_access_denied_fix_response('fix401resp', alb_construct.https_listener)
        template = get_template(app, stack.stack_name)
        print(template)
