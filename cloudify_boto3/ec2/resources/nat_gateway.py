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
    EC2.NATGateway
    ~~~~~~~~~~~~~~
    AWS EC2 NAT Gateway interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.ec2 import EC2Base
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'EC2 NAT Gateway Bucket'
NATGATEWAYS = 'NatGateways'
NATGATEWAY_ID = 'NatGatewayId'
NATGATEWAY_IDS = 'NatGatewayIds'
SUBNET_ID = 'SubnetId'
ALLOCATION_ID = 'AllocationId'
ALLOCATION_ID_DEPRECATED = 'allocation_id'
SUBNET_TYPE = 'cloudify.aws.nodes.Subnet'
ELASTICIP_TYPE = 'cloudify.aws.nodes.ElasticIP'


class EC2NatGateway(EC2Base):
    '''
        EC2 NAT Gateway interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        EC2Base.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        params = {NATGATEWAY_IDS: [self.resource_id]}
        try:
            resources = \
                self.client.describe_nat_gateways(**params)
        except ClientError:
            pass
        else:
            return resources.get(NATGATEWAYS)[0] if resources else None

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['State']

    def create(self, params):
        '''
            Create a new AWS EC2 NAT Gateway.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_nat_gateway(**params)
        self.logger.debug('Response: %s' % res)
        return res['NatGateway']

    def delete(self, params=None):
        '''
            Deletes an existing AWS EC2 NAT Gateway.
        '''
        if NATGATEWAY_ID not in params.keys():
            params.update({NATGATEWAY_ID: self.resource_id})
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_nat_gateway(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS EC2 NAT Gateway'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(EC2NatGateway, RESOURCE_TYPE)
@decorators.wait_for_status(
    status_good=['available'],
    status_pending=['pending'])
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS EC2 NAT Gateway'''
    params = resource_config.copy()

    subnet_id = params.get(SUBNET_ID)
    if not subnet_id:
        subnet_id = \
            utils.find_resource_id_by_type(
                ctx.instance, SUBNET_TYPE)
        params.update({SUBNET_ID: subnet_id})

    allocation_id = params.get(ALLOCATION_ID)
    if not allocation_id:
        targ = \
            utils.find_rel_by_node_type(
                ctx.instance,
                ELASTICIP_TYPE)
        if targ:
            allocation_id = \
                targ.target.instance.runtime_properties.get(
                    ALLOCATION_ID_DEPRECATED)
        params.update({ALLOCATION_ID: allocation_id})

    # Actually create the resource
    nat_gateway = iface.create(params)
    utils.update_resource_id(
        ctx.instance, nat_gateway.get(NATGATEWAY_ID))


@decorators.aws_resource(EC2NatGateway, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete(
    status_deleted=['deleted'],
    status_pending=['deleting'])
def delete(iface, resource_config, **_):
    '''Deletes an AWS EC2 NAT Gateway'''
    iface.delete(resource_config)
