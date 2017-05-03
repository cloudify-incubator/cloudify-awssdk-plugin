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
    AWS SQS Queue interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.sqs import SQSBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'SQS Queue'


class SQSQueue(SQSBase):
    '''
        AWS SQS Queue interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        SQSBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        try:
            resource = \
                self.client.list_queues(QueueNamePrefix=self.resource_id)
        except ClientError:
            pass
        else:
            return resource.get('QueueUrls', [None])[0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def create(self, params):
        '''
            Create a new AWS SQS Queue.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_queue(**params)
        self.logger.debug('Response: %s' % res)

        try:
            resource_attributes = \
                self.client.get_queue_attributes(
                    QueueUrl=res['QueueUrl'],
                    AttributeNames=['QueueArn'])
        except ClientError:
            pass
        else:
            res_arn = \
                resource_attributes.get('Attributes', {}).get('QueueArn')

        return res['QueueUrl'], res_arn

    def delete(self, params=None):
        '''
            Deletes an existing AWS SQS Queue.
        '''
        params = params or dict()
        params.update(dict(QueueUrl=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_queue(**params)


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS SQS Queue'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(SQSQueue, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS SQS Queue'''
    # Build API params
    params = resource_config
    # Actually create the resource
    res_id, res_arn = iface.create(params)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_arn)


@decorators.aws_resource(SQSQueue, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    '''Deletes an AWS SQS Queue'''
    iface.delete(resource_config)
