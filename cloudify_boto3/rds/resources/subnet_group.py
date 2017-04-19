'''
    RDS.SubnetGroup
    ~~~~~~~~~~~~~~~
    AWS RDS subnet group interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.rds import RDSBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'RDS Subnet Group'


class SubnetGroup(RDSBase):
    '''
        AWS RDS Subnet Group interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        RDSBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        resources = None
        try:
            resources = self.client.describe_db_subnet_groups(
                DBSubnetGroupName=self.resource_id)
        except ClientError:
            pass
        if not resources or not resources.get('DBSubnetGroups', list()):
            return None
        return resources['DBSubnetGroups'][0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['SubnetGroupStatus']

    def create(self, params):
        '''
            Create a new AWS RDS subnet group.
        .. note:
            See http://bit.ly/2ownCxX for config details.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_db_subnet_group(**params)
        self.logger.debug('Response: %s' % res)
        self.resource_id = res['DBSubnetGroup']['DBSubnetGroupName']
        return self.resource_id

    def delete(self, params=None):
        '''
            Deletes an existing AWS RDS subnet group.
        .. note:
            See http://bit.ly/2pC0sWj for config details.
        '''
        params = params or dict()
        params.update(dict(DBSubnetGroupName=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_db_subnet_group(**params)


@decorators.aws_resource(SubnetGroup, RESOURCE_TYPE)
@decorators.wait_for_status(status_good=['Complete'])
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS RDS Subnet Group'''
    # Build API params
    params = resource_config
    params.update(dict(DBSubnetGroupName=iface.resource_id))
    # Find connected subnets
    subnet_ids = params.get('SubnetIds', list())
    for rel in utils.find_rels_by_node_type(
            ctx.instance, 'cloudify.aws.nodes.Subnet'):
        subnet_ids.append(
            utils.get_resource_id(
                node=rel.target.node,
                instance=rel.target.instance,
                raise_on_missing=True))
    params['SubnetIds'] = subnet_ids
    # Actually create the resource
    utils.update_resource_id(ctx.instance, iface.create(params))


@decorators.aws_resource(SubnetGroup, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete()
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS Subnet Group'''
    iface.delete(resource_config)
