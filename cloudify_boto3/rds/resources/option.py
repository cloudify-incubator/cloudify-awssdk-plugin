'''
    RDS.Option
    ~~~~~~~~~~
    AWS RDS option interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils

RESOURCE_TYPE = 'RDS Option'


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def configure(ctx, resource_config, **_):
    '''Configures an AWS RDS Option'''
    params = resource_config
    # Set the resource ID
    params['OptionName'] = utils.get_resource_id(raise_on_missing=True)
    # Find connected security group
    security_groups = params.get('VpcSecurityGroupMemberships', list())
    for rel in utils.find_rels_by_node_type(
            ctx.instance, 'cloudify.aws.nodes.SecurityGroup'):
        security_groups.append(
            utils.get_resource_id(
                node=rel.target.node,
                instance=rel.target.instance,
                raise_on_missing=True))
    params['VpcSecurityGroupMemberships'] = security_groups
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = params
