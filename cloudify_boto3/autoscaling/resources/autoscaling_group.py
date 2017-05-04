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
    Autoscaling.Group
    ~~~~~~~~~~~~~~
    AWS Autoscaling Group interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.autoscaling import AutoscalingBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'Autoscaling Group'
GROUPS = 'AutoScalingGroups'
GROUP_NAMES = 'AutoScalingGroupNames'
GROUP_NAME = 'AutoScalingGroupName'
GROUP_ARN = 'AutoScalingGroupARN'
LC_NAME = 'LaunchConfigurationName'
LC_TYPE = 'cloudify.nodes.aws.autoscaling.LaunchConfiguration'
INSTANCE_ID = 'InstanceId'
INSTANCE_IDS = 'InstanceIds'
INSTANCE_TYPE = 'cloudify.aws.nodes.Instance'
INSTANCES = 'Instances'
SUBNET_LIST = 'VPCZoneIdentifier'
SUBNET_TYPE = 'cloudify.aws.nodes.Subnet'


class AutoscalingGroup(AutoscalingBase):
    '''
        Autoscaling Group interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        AutoscalingBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        params = {GROUP_NAMES: [self.resource_id]}
        try:
            resources = \
                self.client.describe_auto_scaling_groups(**params)
        except ClientError:
            pass
        else:
            return resources.get(GROUPS, [None])[0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props.get('Status')

    def create(self, params):
        '''
            Create a new AWS Autoscaling Group.
        '''
        if not self.resource_id:
            setattr(self, 'resource_id', params.get(GROUP_NAME))
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_auto_scaling_group(**params)
        self.logger.debug('Response: %s' % res)
        autoscaling_group = self.properties
        res_id = autoscaling_group.get(GROUP_NAME)
        res_arn = autoscaling_group.get(GROUP_ARN)
        return res_id, res_arn

    def delete(self, params=None):
        '''
            Deletes an existing AWS Autoscaling Group.
        '''
        if GROUP_NAME not in params.keys():
            params.update({GROUP_NAME: self.resource_id})

        autoscaling_group = self.properties
        instances = autoscaling_group.get(INSTANCES)
        self.remove_instances(
            {GROUP_NAME: params.get(GROUP_NAME),
             'ShouldDecrementDesiredCapacity': False,
             INSTANCE_IDS:
                 [instance.get(INSTANCE_ID) for instance in instances]})
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_auto_scaling_group(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def remove_instances(self, params=None):
        '''
            Deletes an existing AWS Autoscaling Group.
        '''
        self.logger.debug('Removing %s with parameters: %s'
                          % (self.type_name, params))
        try:
            res = self.client.detach_instances(**params)
        except ClientError:
            pass
        else:
            self.logger.debug('Response: %s' % res)
            return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS Autoscaling Group'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(AutoscalingGroup, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS Autoscaling Group'''
    params = resource_config.copy()

    # Try to populate the Launch Configuration field
    # with a relationship
    lc_name = params.get(LC_NAME)
    instance_id = params.get(INSTANCE_ID)

    if not lc_name and not instance_id:
        lc_name = \
            utils.find_resource_id_by_type(
                ctx.instance,
                LC_TYPE)
        if lc_name:
            params.update({LC_NAME: lc_name})

    # If no LC_NAME, try to populate the
    # InstanceId field with a relationship.
    if not lc_name:
        instance_id = \
            utils.find_resource_id_by_type(
                ctx.instance,
                INSTANCE_TYPE)
        params[INSTANCE_ID] = instance_id

    subnet_list = params.get(SUBNET_LIST, '')
    subnet_list = \
        utils.add_resources_from_rels(
            ctx.instance,
            SUBNET_TYPE,
            subnet_list.split(', ') if subnet_list else [])
    if subnet_list:
        params[SUBNET_LIST] = ', '.join(subnet_list)

    utils.update_resource_id(
        ctx.instance, params.get(GROUP_NAME))
    # Actually create the resource
    resource_id, resource_arn = iface.create(params)
    utils.update_resource_id(
        ctx.instance, resource_id)
    utils.update_resource_arn(
        ctx.instance, resource_arn)


@decorators.aws_resource(AutoscalingGroup, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    '''Deletes an AWS Autoscaling Group'''
    iface.delete(resource_config)
