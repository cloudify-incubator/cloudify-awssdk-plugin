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
    EC2.VPC
    ~~~~~~~~~~~~~~
    AWS EC2 VPC interface
'''
# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.ec2 import EC2Base
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'EC2 Vpc'
VPC = 'Vpc'
VPCS = 'Vpcs'
VPC_ID = 'VpcId'
VPC_IDS = 'VpcIds'
CIDR_BLOCK = 'CidrBlock'


class EC2Vpc(EC2Base):
    '''
        EC2 Vpc interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        EC2Base.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        params = {VPC_IDS: [self.resource_id]}
        try:
            resources = \
                self.client.describe_vpcs(**params)
        except ClientError:
            pass
        else:
            return None if not resources else resources.get(VPCS, [None])[0]
        return None

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['State']

    def create(self, params):
        '''
            Create a new AWS EC2 Vpc.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_vpc(**params)
        self.logger.debug('Response: %s' % res)
        return res[VPC]

    def delete(self, params=None):
        '''
            Deletes an existing AWS EC2 VPC.
        '''
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_vpc(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(EC2Vpc, resource_type=RESOURCE_TYPE)
def prepare(ctx, iface, resource_config, **_):
    '''Prepares an AWS EC2 Vpc'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(EC2Vpc, RESOURCE_TYPE)
@decorators.wait_for_status(status_good=['available'],
                            status_pending=['pending'])
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS EC2 Vpc'''
    params = \
        dict() if not resource_config else resource_config.copy()

    vpc = iface.create(params)
    vpc_id = vpc.get(VPC_ID, '')
    iface.update_resource_id(vpc_id)
    utils.update_resource_id(
        ctx.instance, vpc_id)


@decorators.aws_resource(EC2Vpc, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    '''Deletes an AWS EC2 Vpc'''

    params = \
        dict() if not resource_config else resource_config.copy()

    if VPC_ID not in params.keys():
        params.update({VPC_ID: iface.resource_id})

    iface.delete(params)
