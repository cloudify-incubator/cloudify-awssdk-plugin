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
    ELB.load_balancer
    ~~~~~~~~~~~~
    AWS ELB load balancer interface
'''
# Cloudify
# from cloudify.exceptions import NonRecoverableError
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.elb import ELBBase
from cloudify_boto3.common.connection import Boto3Connection
from cloudify_boto3.common.constants import (
    EXTERNAL_RESOURCE_ARN,
    EXTERNAL_RESOURCE_ID
)
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'ELB Load Balancer'
LB_NAME = 'LoadBalancerName'
LB_ARN = 'LoadBalancerArn'
LB_ATTR = 'Attributes'
SUBNET_TYPE = 'cloudify.aws.nodes.Subnet'
SECGROUP_TYPE = 'cloudify.aws.nodes.SecurityGroup'
SUBNETS = 'Subnets'
SECGROUPS = 'SecurityGroups'


class ELBLoadBalancer(ELBBase):
    '''
        AWS ELB load balancer interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        ELBBase.__init__(
            self,
            ctx_node,
            resource_id,
            client or Boto3Connection(ctx_node).client('elbv2'),
            logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        try:
            resources = self.client.describe_load_balancers(
                Names=[self.resource_id])
        except ClientError:
            pass
        else:
            return None \
                if not resources else resources['LoadBalancers'][0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['State']['Code']

    def create(self, params):
        '''
            Create a new AWS ELB load balancer.
        .. note:
            See http://bit.ly/2pwMHtb for config details.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_load_balancer(**params)
        self.logger.debug('Response: %s' % res)
        self.update_resource_id(res['LoadBalancers'][0][LB_NAME])
        return self.resource_id, res['LoadBalancers'][0][LB_ARN]

    def delete(self, params=None):
        '''
            Deletes an existing ELB load balancer.
        .. note:
            See http://bit.ly/2pwRpY9 for config details.
        '''
        if LB_ARN not in params.keys():
            params.update({LB_ARN: self.properties.get(LB_ARN)})
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_load_balancer(**params)

    def modify_attribute(self, params):
        '''
            Modify a AWS ELB load balancer attributes.
        .. note:
            See http://bit.ly/2pwMHtb for config details.
        '''
        self.logger.debug('Modifying %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.modify_load_balancer_attributes(**params)
        self.logger.debug('Response: %s' % res)
        return res[LB_ATTR]


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an ELB load balancer'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(ELBLoadBalancer, RESOURCE_TYPE)
@decorators.wait_for_status(
    status_good=['active'],
    status_pending=['provisioning'])
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS ELB load balancer'''
    # Build API params
    cfg = \
        ctx.instance.runtime_properties['resource_config'] or resource_config
    # LB attributes are only applied in modify operation.
    params = cfg.copy()
    params.pop(LB_ATTR, {})
    # Add Subnets
    subnets_from_params = params.get(SUBNETS, [])
    subnets = \
        utils.find_rels_by_node_type(
            ctx.instance,
            SUBNET_TYPE)
    for subnet in subnets:
        subnet_id = \
            subnet.target.instance.runtime_properties[EXTERNAL_RESOURCE_ID]
        subnets_from_params.append(subnet_id)
    params[SUBNETS] = subnets_from_params
    # Add Security Groups
    secgroups_from_params = params.get(SECGROUPS, [])
    secgroups = \
        utils.find_rels_by_node_type(
            ctx.instance,
            SECGROUP_TYPE)
    for secgroup in secgroups:
        secgroup_id = \
            secgroup.target.instance.runtime_properties[EXTERNAL_RESOURCE_ID]
        secgroups_from_params.append(secgroup_id)
    params[SECGROUPS] = secgroups_from_params

    if iface.resource_id and 'Name' not in params.keys():
        params.update(dict(Name=iface.resource_id))
    # Actually create the resource
    iface.create(params)


@decorators.aws_resource(ELBLoadBalancer,
                         RESOURCE_TYPE)
def modify(ctx, iface, resource_config, **_):
    '''modify an AWS ELB load balancer attributes'''
    params = \
        ctx.instance.runtime_properties['resource_config'] \
        or resource_config
    if LB_ARN not in params.keys():
        params.update(
            {LB_ARN: ctx.instance.runtime_properties.get(
                EXTERNAL_RESOURCE_ARN)})
    modify_params_attributes = params.pop(LB_ATTR, {})
    if modify_params_attributes:
        # Add the LB ARN
        modify_params = {}
        modify_params[LB_ARN] = params.get(LB_ARN)
        modify_params[LB_ATTR] = modify_params_attributes
        # Actually modify the resource
        attributes = iface.modify_attribute(modify_params)
        ctx.instance.runtime_properties['resource_config'][LB_ATTR] = \
            attributes


@decorators.aws_resource(ELBLoadBalancer, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete(status_pending=[])
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS ELB load balancer'''
    iface.delete(resource_config)
