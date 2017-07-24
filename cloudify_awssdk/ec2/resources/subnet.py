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
    EC2.Subnet
    ~~~~~~~~~~~~~~
    AWS EC2 Subnet interface
'''
# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.ec2 import EC2Base
from cloudify_awssdk.common.constants import EXTERNAL_RESOURCE_ID
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'EC2 Subnet'
SUBNET = 'Subnet'
SUBNETS = 'Subnets'
SUBNET_ID = 'SubnetId'
SUBNET_IDS = 'SubnetIds'
CIDR_BLOCK = 'CidrBlock'
VPC_ID = 'VpcId'
VPC_TYPE = 'cloudify.nodes.aws.ec2.Vpc'
VPC_TYPE_DEPRECATED = 'cloudify.aws.nodes.Vpc'


class EC2Subnet(EC2Base):
    '''
        EC2 Subnet interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        EC2Base.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        params = {SUBNET_IDS: [self.resource_id]}
        try:
            resources = \
                self.client.describe_subnets(**params)
        except ClientError:
            pass
        else:
            return None if not resources else resources.get(SUBNETS)[0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['State']

    def create(self, params):
        '''
            Create a new AWS EC2 Subnet.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_subnet(**params)
        self.logger.debug('Response: %s' % res)
        return res[SUBNET]

    def delete(self, params=None):
        '''
            Deletes an existing AWS EC2 Subnet.
        '''
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_subnet(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(EC2Subnet, resource_type=RESOURCE_TYPE)
def prepare(ctx, iface, resource_config, **_):
    '''Prepares an AWS EC2 Subnet'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(EC2Subnet, RESOURCE_TYPE)
@decorators.wait_for_status(status_good=['available'],
                            status_pending=['pending'])
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS EC2 Subnet'''
    params = dict() if not resource_config else resource_config.copy()

    vpc_id = params.get(VPC_ID)
    cidr_block = params.get(CIDR_BLOCK)

    # If either of these values is missing,
    # they must be filled from a connected VPC.
    if not vpc_id or not cidr_block:
        targ = \
            utils.find_rel_by_node_type(
                ctx.instance,
                VPC_TYPE) or utils.find_rel_by_node_type(
                ctx.instance,
                VPC_TYPE_DEPRECATED)

        # Attempt to use the VPC ID from parameters.
        # Fallback to connected VPC.
        params[VPC_ID] = \
            vpc_id or \
            targ.target.instance.runtime_properties.get(
                EXTERNAL_RESOURCE_ID)
        # Attempt to use the CIDR Block from parameters.
        # Fallback to connected VPC.
        params[CIDR_BLOCK] = \
            cidr_block or \
            targ.instance.runtime_properties.get(
                'resource_config', {}).get(CIDR_BLOCK)

    subnet = iface.create(params)
    subnet_id = subnet.get(SUBNET_ID)
    iface.update_resource_id(subnet_id)
    utils.update_resource_id(ctx.instance, subnet_id)


@decorators.aws_resource(EC2Subnet, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS EC2 Subnet'''
    params = \
        dict() if not resource_config else resource_config.copy()

    subnet_id = params.get(SUBNET_ID)
    if not subnet_id:
        params[SUBNET_ID] = \
            iface.resource_id or \
            ctx.instance.runtime_properties.get(EXTERNAL_RESOURCE_ID)

    iface.delete(params)
