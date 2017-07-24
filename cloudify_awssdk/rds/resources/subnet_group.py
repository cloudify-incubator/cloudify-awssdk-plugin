# #######
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
'''
    RDS.SubnetGroup
    ~~~~~~~~~~~~~~~
    AWS RDS subnet group interface
'''
# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.rds import RDSBase
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
        self.update_resource_id(res['DBSubnetGroup']['DBSubnetGroupName'])
        return self.resource_id, res['DBSubnetGroup']['DBSubnetGroupArn']

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


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS RDS Subnet Group'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(SubnetGroup, RESOURCE_TYPE)
@decorators.wait_for_status(status_good=['Complete'])
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS RDS Subnet Group'''
    # Build API params
    params = ctx.instance.runtime_properties['resource_config'] or dict()
    params.update(dict(DBSubnetGroupName=iface.resource_id))
    # Actually create the resource
    res_id, res_arn = iface.create(params)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_arn)


@decorators.aws_resource(SubnetGroup, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete()
def delete(iface, resource_config, **_):
    '''Deletes an AWS Subnet Group'''
    iface.delete(resource_config)


@decorators.aws_relationship(SubnetGroup, RESOURCE_TYPE)
def prepare_assoc(ctx, iface, resource_config, **_):
    '''Prepares to associate an RDS SubnetGroup to something else'''
    if utils.is_node_type(ctx.target.node,
                          'cloudify.aws.nodes.Subnet'):
        subnet_ids = ctx.source.instance.runtime_properties[
            'resource_config'].get('SubnetIds', list())
        subnet_ids.append(
            utils.get_resource_id(
                node=ctx.target.node,
                instance=ctx.target.instance,
                raise_on_missing=True))
        ctx.source.instance.runtime_properties[
            'resource_config']['SubnetIds'] = subnet_ids


@decorators.aws_relationship(SubnetGroup, RESOURCE_TYPE)
def detach_from(ctx, iface, resource_config, **_):
    '''Detaches an RDS SubnetGroup from something else'''
    pass
