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
    CloudFormation.stack
    ~~~~~~~~~~~~~~
    AWS CloudFormation Stack interface
"""
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.cloudformation import AWSCloudFormationBase
# Boto
from botocore.exceptions import ClientError

import json

RESOURCE_TYPE = 'CloudFormation Stack'
NAME = 'StackName'
NAMES = 'StackNames'
STACKS = 'Stacks'
TEMPLATEBODY = 'TemplateBody'


class CloudFormationStack(AWSCloudFormationBase):
    """
        AWS CloudFormation Stack interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        AWSCloudFormationBase.__init__(self, ctx_node, resource_id, client,
                                       logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        params = {NAME: self.resource_id}
        try:
            resources = \
                self.client.describe_stacks(**params)
        except ClientError:
            pass
        else:
            return resources.get(STACKS, [None])[0]

    @property
    def status(self):
        """Gets the status of an external resource"""
        props = self.properties
        if not props:
            return None
        return None

    def create(self, params):
        """
            Create a new AWS CloudFormation Stack.
        """
        if not self.resource_id:
            setattr(self, 'resource_id', params.get(NAME))
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_stack(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def delete(self, params=None):
        """
            Deletes an existing AWS CloudFormation Stack.
        """
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_stack(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an AWS CloudFormation Stack"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(CloudFormationStack, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    """Creates an AWS CloudFormation Stack"""
    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()

    stack_name = params.get(NAME)
    utils.update_resource_id(ctx.instance, stack_name)

    template_body = params.get(TEMPLATEBODY, {})
    if not isinstance(template_body, basestring):
        params[TEMPLATEBODY] = json.dumps(template_body)

    # Actually create the resource
    iface.create(params)


@decorators.aws_resource(CloudFormationStack, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    """Deletes an AWS CloudFormation Stack"""
    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()
    name = params.get(NAME)
    if not name:
        name = iface.resource_id
    iface.delete({NAME: name})
