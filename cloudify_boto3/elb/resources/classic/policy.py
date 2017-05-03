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
    ELB.classic.policy
    ~~~~~~~~~~~~
    AWS ELB classic policy interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.elb import ELBBase
from cloudify_boto3.common.connection import Boto3Connection
from cloudify_boto3.common.constants import EXTERNAL_RESOURCE_ID

RESOURCE_TYPE = 'ELB classic policy'
POLICY_NAME = 'PolicyName'
LB_NAME = 'LoadBalancerName'
LB_TYPE = 'cloudify.nodes.aws.elb.Classic.LoadBalancer'


class ELBClassicPolicy(ELBBase):
    '''
        AWS ELB classic policy interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        ELBBase.__init__(
            self,
            ctx_node,
            resource_id,
            client or Boto3Connection(ctx_node).client('elb'),
            logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        return None

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['State']['Code']

    def create(self, params, sticky=False):
        '''
            Create a new AWS ELB classic policy.
        .. note:
            See http://bit.ly/2oYIQrZ for config details.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        if sticky:
            res = \
                self.client.create_lb_cookie_stickiness_policy(**params)
        else:
            res = \
                self.client.create_load_balancer_policy(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def delete(self, params=None):
        '''
            Deletes an existing ELB classic policy.
        .. note:
            See http://bit.ly/2qGiN5e for config details.
        '''
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        return self.client.delete_load_balancer_policy(**params)


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an ELB classic policy'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(ELBClassicPolicy, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS ELB classic policy'''
    # Build API params
    params = \
        ctx.instance.runtime_properties['resource_config'] or resource_config

    if LB_NAME not in params:
        targs = \
            utils.find_rels_by_node_type(
                ctx.instance,
                LB_TYPE)
        lb_name = \
            targs[0].target.instance.runtime_properties[
                EXTERNAL_RESOURCE_ID]
        ctx.instance.runtime_properties[LB_NAME] = \
            lb_name
        params.update({LB_NAME: lb_name})
    ctx.instance.runtime_properties[POLICY_NAME] = \
        params.get(POLICY_NAME)
    # Actually create the resource
    iface.create(params)


@decorators.aws_resource(ELBClassicPolicy, RESOURCE_TYPE)
def create_lb_stickiness(ctx, iface, resource_config, **_):
    '''Creates an AWS ELB classic policy'''
    # Build API params
    params = \
        ctx.instance.runtime_properties['resource_config'] or resource_config

    if LB_NAME not in params:
        targs = \
            utils.find_rels_by_node_type(
                ctx.instance,
                LB_TYPE)
        lb_name = \
            targs[0].target.instance.runtime_properties[
                EXTERNAL_RESOURCE_ID]
        ctx.instance.runtime_properties[LB_NAME] = \
            lb_name
        params.update({LB_NAME: lb_name})
    ctx.instance.runtime_properties[POLICY_NAME] = \
        params.get(POLICY_NAME)
    # Actually create the resource
    iface.create(params, sticky=True)


@decorators.aws_resource(ELBClassicPolicy, RESOURCE_TYPE)
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS ELB classic policy'''
    lb = resource_config.get(LB_NAME) \
        or ctx.instance.runtime_properties.get(LB_NAME)
    policy = resource_config[POLICY_NAME]
    iface.delete({LB_NAME: lb, POLICY_NAME: policy})
