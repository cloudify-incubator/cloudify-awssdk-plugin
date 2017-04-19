'''
    RDS.OptionGroup
    ~~~~~~~~~~~~~~~
    AWS RDS parameter group interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.rds import RDSBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'RDS Parameter Group'


class ParameterGroup(RDSBase):
    '''
        AWS RDS Parameter Group interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        RDSBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        resources = None
        try:
            resources = self.client.describe_db_parameter_groups(
                DBParameterGroupName=self.resource_id)
        except ClientError:
            pass
        if not resources or not resources.get('DBParameterGroups', list()):
            return None
        return resources['DBParameterGroups'][0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def update_parameter(self, param):
        '''Adds a parameter to an AWS RDS parameter group'''
        return self.update(dict(Parameters=[param]))

    def update(self, params):
        '''Updates an existing AWS RDS parameter group'''
        params['DBParameterGroupName'] = self.resource_id
        self.logger.debug('Modifying parameter group: %s' % params)
        res = self.client.modify_db_parameter_group(**params)
        self.logger.debug('Response: %s' % res)
        return res['DBParameterGroupName']

    def create(self, params):
        '''
            Create a new AWS RDS parameter group.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_db_parameter_group(**params)
        self.logger.debug('Response: %s' % res)
        self.resource_id = res['DBParameterGroup']['DBParameterGroupName']
        return self.resource_id

    def delete(self, params=None):
        '''
            Deletes an existing AWS RDS parameter group.
        '''
        params = params or dict()
        params.update(dict(DBParameterGroupName=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_db_parameter_group(**params)


@decorators.aws_resource(ParameterGroup, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS RDS Parameter Group'''
    # Build API params
    resource_config.update(dict(DBParameterGroupName=iface.resource_id))
    # Actually create the resource
    utils.update_resource_id(ctx.instance, iface.create(resource_config))


@decorators.aws_resource(ParameterGroup, RESOURCE_TYPE)
def configure(ctx, iface, resource_config, **_):
    '''Configures an AWS RDS Parameter Group'''
    if not resource_config:
        return
    # Actually create the resource
    iface.update(resource_config)


@decorators.aws_resource(ParameterGroup, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete(status_pending=['available'])
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS Parameter Group'''
    iface.delete(resource_config)


def update_parameter(ctx):
    '''Updates a parameter in a parameter group'''
    ctx.logger.debug('Param RTA: %s' %
                     ctx.target.instance.runtime_properties['resource_config'])
    ParameterGroup(
        ctx.source.node, logger=ctx.logger,
        resource_id=utils.get_resource_id(
            node=ctx.source.node,
            instance=ctx.source.instance,
            raise_on_missing=True)
    ).update_parameter(
        ctx.target.instance.runtime_properties['resource_config'])
