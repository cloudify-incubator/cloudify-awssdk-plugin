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
    CloudwatchLogs.log_group
    ~~~~~~~~~~~~~~
    AWS Cloudwatch Logs Log Group interface
"""
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.cloudwatchlogs import AWSCloudwatchLogsBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'Cloudwatch Logs Log Group'
RESOURCE_NAME = 'logGroupName'
RESOURCES = 'logGroups'
SEARCH_KEY = 'logGroupNamePrefix'


class CloudwatchLogGroup(AWSCloudwatchLogsBase):
    """
        AWS AWS Cloudwatch Log Group interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        AWSCloudwatchLogsBase.__init__(
            self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        params = {SEARCH_KEY: self.resource_id}
        try:
            resources = \
                self.client.describe_alarms(**params)
        except ClientError:
            pass
        else:
            return resources.get(RESOURCES, [None])[0]

    @property
    def status(self):
        """Gets the status of an external resource"""
        props = self.properties
        if not props:
            return None
        return None

    def create(self, params):
        """
            Create a new AWS Cloudwatch Log Group.
        """
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_log_group(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def delete(self, params=None):
        """
            Deletes an existing AWS Cloudwatch Log Group.
        """
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_log_group(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an AWS Cloudwatch Log Group"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(CloudwatchLogGroup, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    """Creates an AWS Cloudwatch Log Group"""
    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()
    resource_id = \
        iface.resource_id or \
        utils.get_resource_id(
            ctx.node,
            ctx.instance,
            params.get(RESOURCE_NAME),
            use_instance_id=True)
    params[RESOURCE_NAME] = resource_id
    utils.update_resource_id(ctx.instance, resource_id)

    # Actually create the resource
    iface.create(params)


@decorators.aws_resource(CloudwatchLogGroup, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    """Deletes an AWS Cloudwatch Log Group"""
    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()
    if RESOURCE_NAME not in params.keys():
        params.update({RESOURCE_NAME: iface.resource_id})
    iface.delete(params)
