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
    SQS.subscription
    ~~~~~~~~
    AWS SNS Subscription interface
'''
# Generic
import re
# Cloudify
from cloudify.exceptions import NonRecoverableError
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.sns import SNSBase
from cloudify_boto3.common.constants import EXTERNAL_RESOURCE_ARN
from .topic import SNSTopic
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'SNS Subscription'
SUB_ARN = 'SubscriptionArn'
TOPIC_TYPE = 'cloudify.nodes.aws.SNS.Topic'
TOPIC_ARN = 'TopicArn'
ARN_REGEX = '^arn\:aws\:'
ARN_MATCHER = re.compile(ARN_REGEX)


class SNSSubscription(SNSBase):
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
                self.client.list_subscriptions()
        except ClientError:
            pass
        else:
            for resource in resources:
                if resource[SUB_ARN] == self.resource_id:
                    return resource
        return None

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def confirm(self, params):
        '''
            Confirms a AWS SNS Subscription request was successful.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.get_subscription_attributes(**params)
        self.logger.debug('Response: %s' % res)
        return res['Attributes']

    def delete(self, params=None):
        '''
            Deletes an existing AWS SNS Subscription.
        '''
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.unsubscribe(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS SNS Topic'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(SNSSubscription, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS SNS Subscription'''

    # Subscribe and Confirm require TopicArn argument
    if TOPIC_ARN not in resource_config:
        rel = \
            utils.find_rel_by_node_type(
                ctx.instance,
                TOPIC_TYPE)
        topic_arn = \
            rel.target.instance.runtime_properties.get(
                EXTERNAL_RESOURCE_ARN)
        topic_iface = SNSTopic(
            ctx_node=rel.target.node,
            resource_id=topic_arn,
            client=iface.client,
            logger=ctx.logger)
        ctx.instance.runtime_properties[TOPIC_ARN] = \
            topic_arn
        resource_config[TOPIC_ARN] = topic_arn

    # Subscribe Endpoint is the arn of an endpoint
    endpoint_name = resource_config.get('Endpoint')
    if not endpoint_name:
        raise NonRecoverableError(
            'Endpoint ARN or node_name was not provided.')
    if not ARN_MATCHER.match(endpoint_name):
        rel = \
            utils.find_rels_by_node_name(
                ctx.instance,
                endpoint_name)[0]
        endpoint_arn = \
            rel.target.instance.runtime_properties.get(
                EXTERNAL_RESOURCE_ARN)
        resource_config['Endpoint'] = endpoint_arn

    # Request the subscription
    request_arn = topic_iface.subscribe(resource_config)
    utils.update_resource_id(ctx.instance, request_arn)
    utils.update_resource_arn(ctx.instance, request_arn)


@decorators.aws_resource(SNSSubscription,
                         RESOURCE_TYPE,
                         ignore_properties=True)
def start(ctx, iface, resource_config, **_):
    '''Confirm an AWS SNS Subscription'''
    if SUB_ARN not in resource_config:
        arn = ctx.instance.runtime_properties.get(
            EXTERNAL_RESOURCE_ARN)
        resource_config[SUB_ARN] = arn
    sub_attributes = iface.confirm(resource_config)
    if 'ConfirmationWasAuthenticated' not in sub_attributes:
        return ctx.operation.retry('Confirmation not authenticated.')


@decorators.aws_resource(SNSSubscription, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS SNS Subscription'''
    if SUB_ARN not in resource_config:
        arn = ctx.instance.runtime_properties.get(
            EXTERNAL_RESOURCE_ARN)
        resource_config[SUB_ARN] = arn
    iface.delete(resource_config)
