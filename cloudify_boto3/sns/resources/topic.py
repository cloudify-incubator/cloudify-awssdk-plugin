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
    SQS.queue
    ~~~~~~~~
    AWS SNS Topic interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.sns import SNSBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'SNS Topic'
SUB_ARN = 'SubscriptionArn'


class SNSTopic(SNSBase):
    '''
        AWS SQS Queue interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        SNSBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        try:
            resources = \
                self.client.list_topics()
        except ClientError:
            pass
        else:
            for resource in resources:
                resource_arn = resource.get('TopicArn')
                if self.resource_id == resource_arn:
                    return resource_arn
            return None

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def create(self, params):
        '''
            Create a new AWS SNS Topic.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_topic(**params)
        self.logger.debug('Response: %s' % res)
        return res['TopicArn']

    def subscribe(self, params):
        '''
            Subscribing to AWS SNS Topic.
        '''
        self.logger.debug('Subscribing %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.subscribe(**params)
        self.logger.debug('Response: %s' % res)
        return res[SUB_ARN]

    def delete(self, params=None):
        '''
            Deletes an existing AWS SNS Topic.
        '''
        params = params or dict()
        params.update(dict(TopicArn=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_topic(**params)


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS SNS Topic'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(SNSTopic, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS SNS Topic'''
    # Build API params
    params = resource_config
    # Actually create the resource
    res_id = iface.create(params)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_id)


@decorators.aws_resource(SNSTopic, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    '''Deletes an AWS SNS Topic'''
    iface.delete(resource_config)
