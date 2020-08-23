import json

from aws_cdk import (
    core,
    aws_ec2
)


def get_template(app: core.App, stack_name: str):
    template = app.synth().get_stack_by_name(stack_name).template
    return json.dumps(template)


class GenericTestStack(core.Stack):
    vpc: aws_ec2.IVpc
    subnets: aws_ec2.SubnetSelection

    def __init__(self, scope: core.Construct, sid: str, **kwargs) -> None:
        super().__init__(scope, sid, **kwargs)
        self.vpc = aws_ec2.Vpc(self, 'TestVPC', cidr='10.0.0.0/16')
        self.subnets = aws_ec2.SubnetSelection(subnets=self.vpc.select_subnets(one_per_az=True).subnets)
