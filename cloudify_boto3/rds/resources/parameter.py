'''
    RDS.Parameter
    ~~~~~~~~~~~~~
    AWS RDS parameter interface
'''
# Cloudify
from cloudify_boto3.common import decorators

RESOURCE_TYPE = 'RDS Parameter'


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def configure(ctx, resource_config, **_):
    '''Configures an AWS RDS Parameter'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config
