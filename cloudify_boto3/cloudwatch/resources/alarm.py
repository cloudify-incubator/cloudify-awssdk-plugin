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
    Cloudwatch.alarm
    ~~~~~~~~~~~~~~
    AWS Cloudwatch Alarm interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.cloudwatch import AWSCloudwatchBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'Cloudwatch Alarm'
NAME = 'AlarmName'
NAMES = 'AlarmNames'
METRIC_ALARMS = 'MetricAlarms'


class CloudwatchAlarm(AWSCloudwatchBase):
    '''
        AWS Cloudwatch Alarm interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        AWSCloudwatchBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        params = {NAMES: [self.resource_id]}
        try:
            resources = \
                self.client.describe_alarms(**params)
        except ClientError:
            pass
        else:
            return resources.get(METRIC_ALARMS, [None])[0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return None

    def create(self, params):
        '''
            Create a new AWS Cloudwatch Alarm.
        '''
        if not self.resource_id:
            setattr(self, 'resource_id', params.get(NAME))
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.put_metric_alarm(**params)
        self.logger.debug('Response: %s' % res)
        return res

    def delete(self, params=None):
        '''
            Deletes an existing AWS Cloudwatch Alarm.
        '''
        if NAMES not in params.keys():
            params.update({NAMES: [self.resource_id]})
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_alarms(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS Cloudwatch Alarm'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(CloudwatchAlarm, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS Cloudwatch Alarm'''
    params = resource_config.copy()
    alarm_name = params.get(NAME)
    utils.update_resource_id(ctx.instance, alarm_name)
    # Actually create the resource
    iface.create(params)


@decorators.aws_resource(CloudwatchAlarm, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS Cloudwatch Alarm'''
    params = resource_config.copy()
    iface.delete(params)
