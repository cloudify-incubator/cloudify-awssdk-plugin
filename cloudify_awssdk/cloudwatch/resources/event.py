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
    Cloudwatch.Events.Event
    ~~~~~~~~~~~~~~
    AWS Cloudwatch Events Event interface
"""
# Cloudify
from cloudify_awssdk.common import decorators
from cloudify_awssdk.cloudwatch import AWSCloudwatchBase
from cloudify_awssdk.common.connection import Boto3Connection

RESOURCE_TYPE = 'Cloudwatch Event'


class CloudwatchEvent(AWSCloudwatchBase):
    """
        AWS Cloudwatch Events Event interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        AWSCloudwatchBase.__init__(
            self,
            ctx_node,
            resource_id,
            client or Boto3Connection(ctx_node).client('events'),
            logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        return None

    @property
    def status(self):
        """Gets the status of an external resource"""
        return None

    def create(self, params):
        """
            Create a new AWS Cloudwatch Events Event.
        """
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.put_events(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def delete(self, params=None):
        return None


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an AWS Cloudwatch Events Event"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(CloudwatchEvent, RESOURCE_TYPE)
def create(iface, resource_config, **_):
    """Creates an AWS Cloudwatch Events Event"""

    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()
    iface.create(params)
