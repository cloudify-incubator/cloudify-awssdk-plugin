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
    RDS.InstanceReadReplica
    ~~~~~~~~~~~~~~~~~~~~~~~
    AWS RDS instance read replica interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.rds import RDSBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'RDS DB Instance Read Replica'


class DBInstanceReadReplica(RDSBase):
    '''
        AWS RDS DB Instance Read Replica interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        RDSBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        resources = None
        try:
            resources = self.client.describe_db_instances(
                DBInstanceIdentifier=self.resource_id)
        except ClientError:
            pass
        if not resources or not resources.get('DBInstances', list()):
            return None
        return resources['DBInstances'][0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['DBInstanceStatus']

    def create(self, params):
        '''
            Create a new AWS RDS DB instance.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_db_instance_read_replica(**params)
        self.logger.debug('Response: %s' % res)
        self.update_resource_id(res['DBInstance']['DBInstanceIdentifier'])
        return self.resource_id, res['DBInstance']['DBInstanceArn']

    def delete(self, params=None):
        '''
            Deletes an existing AWS RDS DB instance.
        .. note:
            See http://bit.ly/2pkNk91 for config details.
        '''
        params = params or dict(SkipFinalSnapshot=True)
        params.update(dict(
            DBInstanceIdentifier=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_db_instance(**params)


@decorators.aws_resource(DBInstanceReadReplica, RESOURCE_TYPE)
@decorators.wait_for_status(status_good=['available'],
                            status_pending=['creating', 'modifying'])
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS RDS Instance RR'''
    # Build API params
    params = resource_config
    params.update(dict(DBInstanceIdentifier=iface.resource_id))
    # Attach a DB Instance if it exists
    dbinstance = utils.find_rel_by_node_type(
        ctx.instance, 'cloudify.nodes.aws.rds.Instance')
    if dbinstance:
        params['SourceDBInstanceIdentifier'] = utils.get_resource_id(
            node=dbinstance.target.node,
            instance=dbinstance.target.instance,
            raise_on_missing=True)
    # Attach a Subnet Group if it exists
    subnet_group = utils.find_rel_by_node_type(
        ctx.instance, 'cloudify.nodes.aws.rds.SubnetGroup')
    if subnet_group:
        params['DBSubnetGroupName'] = utils.get_resource_id(
            node=subnet_group.target.node,
            instance=subnet_group.target.instance,
            raise_on_missing=True)
    # Attach an Option Group if it exists
    option_group = utils.find_rel_by_node_type(
        ctx.instance, 'cloudify.nodes.aws.rds.OptionGroup')
    if option_group:
        params['OptionGroupName'] = utils.get_resource_id(
            node=option_group.target.node,
            instance=option_group.target.instance,
            raise_on_missing=True)
    # Actually create the resource
    res_id, res_arn = iface.create(params)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_arn)


@decorators.aws_resource(DBInstanceReadReplica, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_status(status_pending=['deleting'],
                            fail_on_missing=False)
def delete(iface, resource_config, **_):
    '''Deletes an AWS RDS Instance RR'''
    iface.delete(resource_config)
