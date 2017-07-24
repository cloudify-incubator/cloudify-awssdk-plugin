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
"""
    EC2.NetworkInterface
    ~~~~~~~~~~~~~~
    AWS EC2 NetworkInterface interface
"""
# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.ec2 import EC2Base
from cloudify_awssdk.common.constants import EXTERNAL_RESOURCE_ID
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'EC2 Network Interface'
NETWORKINTERFACES = 'NetworkInterfaces'
NETWORKINTERFACE_ID = 'NetworkInterfaceId'
NETWORKINTERFACE_IDS = 'NetworkInterfaceIds'
INSTANCE_ID = 'InstanceId'
INSTANCE_TYPE_DEPRECATED = 'cloudify.aws.nodes.Instance'
SUBNET_ID = 'SubnetId'
SUBNET_TYPE = 'cloudify.nodes.aws.ec2.Subnet'
SUBNET_TYPE_DEPRECATED = 'cloudify.aws.nodes.Subnet'
ATTACHMENT_ID = 'AttachmentId'


class EC2NetworkInterface(EC2Base):
    """
        EC2 NetworkInterface interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        EC2Base.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        params = {NETWORKINTERFACE_IDS: [self.resource_id]}
        try:
            resources = \
                self.client.describe_network_interfaces(**params)
        except ClientError:
            pass
        else:
            return resources.get(NETWORKINTERFACES)[0] if resources else None

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['Status']

    def create(self, params):
        """
            Create a new AWS EC2 NetworkInterface.
        """
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_network_interface(**params)
        self.logger.debug('Response: %s' % res)
        return res['NetworkInterface']

    def delete(self, params=None):
        """
            Deletes an existing AWS EC2 NetworkInterface.
        """
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_network_interface(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def attach(self, params):
        '''
            Attach an AWS EC2 NetworkInterface to a Subnet.
        '''
        self.logger.debug('Attaching %s with: %s'
                          % (self.type_name, params.get(SUBNET_ID, None)))
        res = self.client.attach_network_interface(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def detach(self, params):
        '''
            Detach an AWS EC2 NetworkInterface from a Subnet.
        '''
        self.logger.debug('Detaching %s from: %s'
                          % (self.type_name, params.get(SUBNET_ID, None)))
        self.logger.debug('Attaching default %s'
                          % (self.type_name))
        res = self.client.detach_network_interface(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an AWS EC2 NetworkInterface"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(EC2NetworkInterface, RESOURCE_TYPE)
@decorators.wait_for_status(status_good=['available'])
def create(ctx, iface, resource_config, **_):
    """Creates an AWS EC2 NetworkInterface"""

    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()

    subnet_id = params.get(SUBNET_ID)
    if not subnet_id:
        targ = \
            utils.find_rel_by_node_type(ctx.instance, SUBNET_TYPE) or \
            utils.find_rel_by_node_type(ctx.instance, SUBNET_TYPE_DEPRECATED)

        # Attempt to use the VPC ID from parameters.
        # Fallback to connected VPC.
        params[SUBNET_ID] = \
            subnet_id or \
            targ.target.instance.runtime_properties.get(EXTERNAL_RESOURCE_ID)

    # Actually create the resource
    eni = iface.create(params)
    eni_id = eni.get(NETWORKINTERFACE_ID, '')
    iface.update_resource_id(eni_id)
    utils.update_resource_id(ctx.instance, eni_id)
    ctx.instance.runtime_properties['device_index'] = \
        ctx.instance.runtime_properties.get('device_index', 1)


@decorators.aws_resource(EC2NetworkInterface, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(ctx, iface, resource_config, **_):
    """Deletes an AWS EC2 NetworkInterface"""

    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()
    eni_id = params.get(NETWORKINTERFACE_ID)

    if not eni_id:
        params[NETWORKINTERFACE_ID] = \
            iface.resource_id or \
            ctx.instance.runtime_properties.get(EXTERNAL_RESOURCE_ID)

    iface.delete(params)


@decorators.aws_resource(EC2NetworkInterface, RESOURCE_TYPE)
def attach(ctx, iface, resource_config, **_):
    '''Attaches an AWS EC2 NetworkInterface to a Subnet'''
    params = dict() if not resource_config else resource_config.copy()

    eni_id = params.get(NETWORKINTERFACE_ID)
    if not eni_id:
        eni_id = iface.resource_id

    device_index = ctx.instance.runtime_properties.get('device_index', 1)
    ctx.instance.runtime_properties['device_index'] = device_index

    params.update({NETWORKINTERFACE_ID: eni_id})
    params.update({'DeviceIndex': device_index})

    instance_id = params.get(INSTANCE_ID)
    if not instance_id:
        targ = \
            utils.find_rel_by_node_type(ctx.instance, INSTANCE_TYPE_DEPRECATED)

        # Attempt to use the SUBNET ID from parameters.
        # Fallback to connected SUBNET.
        if not targ:
            return

        params[INSTANCE_ID] = \
            instance_id or \
            targ.target.instance.runtime_properties.get(EXTERNAL_RESOURCE_ID)

    # Actually attach the resources
    eni_attachment_id = iface.attach(params)
    ctx.instance.runtime_properties['attachment_id'] = \
        eni_attachment_id[ATTACHMENT_ID]


@decorators.aws_resource(EC2NetworkInterface, RESOURCE_TYPE,
                         ignore_properties=True)
def detach(ctx, iface, resource_config, **_):
    '''Detach an AWS EC2 NetworkInterface from a Subnet'''
    params = dict() if not resource_config else resource_config.copy()

    attachment_id = ctx.instance.runtime_properties.get('attachment_id', None)
    if not attachment_id:
        return

    params.update({ATTACHMENT_ID: attachment_id})
    iface.detach(params)
