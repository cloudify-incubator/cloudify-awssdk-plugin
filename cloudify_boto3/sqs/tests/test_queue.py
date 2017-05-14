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

from mock import patch, MagicMock
import unittest

from cloudify.state import current_ctx

from botocore.exceptions import UnknownServiceError

from cloudify_boto3.common.tests.test_base import TestBase, CLIENT_CONFIG
from cloudify_boto3.common.tests.test_base import DELETE_RESPONSE

from cloudify_boto3.sqs.resources import queue


# Constants
QUEUE_TH = ['cloudify.nodes.Root',
            'cloudify.nodes.aws.SQS.Queue']

RESOURCE_CONFIG = {
    'QueueName': 'test-queue',
    'Attributes': {
        'Policy': {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "Sid1",
                "Effect": "Deny",
                "Principal": "*",
                "Action": [
                    "SQS:SendMessage",
                    "SQS:ReceiveMessage"
                ],
                "Resource": "test-queue"
            }]
        },
        'MessageRetentionPeriod': '86400',
        'VisibilityTimeout': '180'
    }
}

NODE_PROPERTIES = {
    'use_external_resource': False,
    'resource_config': {
        'kwargs': RESOURCE_CONFIG
    },
    'client_config': CLIENT_CONFIG
}

RUNTIME_PROPERTIES = {
    'resource_config': {
    }
}

RUNTIME_PROPERTIES_AFTER_CREATE = {
    'aws_resource_arn': 'fake_QueueArn',
    'aws_resource_id': 'fake_QueueUrl',
    'resource_config': {}
}

POLICY_STRING = (
    """{"Version": "2012-10-17", "Statement": [{"Action": ["SQS:SendMessag""" +
    """e", "SQS:ReceiveMessage"], "Sid": "Sid1", "Resource": "test-queue",""" +
    """ "Effect": "Deny", "Principal": "*"}]}"""
)


class TestSQSQueue(TestBase):

    def test_prepare(self):
        _ctx = self.get_mock_ctx(
            'test_prepare',
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES,
            type_hierarchy=QUEUE_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('sqs')

        with patch('boto3.client', fake_boto):
            queue.prepare(ctx=_ctx, resource_config=None, iface=None)
            self.assertEqual(
                _ctx.instance.runtime_properties, {
                    'resource_config': RESOURCE_CONFIG
                }
            )

    def test_create_raises_UnknownServiceError(self):
        _ctx = self.get_mock_ctx(
            'test_create',
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES,
            type_hierarchy=QUEUE_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('sqs')

        with patch('boto3.client', fake_boto):
            with self.assertRaises(UnknownServiceError) as error:
                queue.create(ctx=_ctx, resource_config=None, iface=None)

            self.assertEqual(
                str(error.exception),
                "Unknown service: 'sqs'. Valid service names are: ['rds']"
            )

            fake_boto.assert_called_with('sqs', **CLIENT_CONFIG)

    def test_create(self):
        _ctx = self.get_mock_ctx(
            'test_create',
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES,
            type_hierarchy=QUEUE_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('sqs')

        with patch('boto3.client', fake_boto):
            fake_client.create_queue = MagicMock(return_value={
                'QueueUrl': 'fake_QueueUrl'
            })

            queue.create(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('sqs', **CLIENT_CONFIG)

            fake_client.get_queue_attributes.assert_called_with(
                AttributeNames=['QueueArn'], QueueUrl='fake_QueueUrl'
            )

            self.assertEqual(
                _ctx.instance.runtime_properties,
                {
                    'aws_resource_arn': 'None',
                    'aws_resource_id': 'fake_QueueUrl',
                    'resource_config': {}
                }
            )

    def test_create_with_arn(self):
        node_properties = {
            'use_external_resource': False,
            'resource_config': {
                'kwargs': {
                    'QueueName': 'test-queue',
                    'Attributes': {
                        'Policy': POLICY_STRING,
                        'MessageRetentionPeriod': '86400',
                        'VisibilityTimeout': '180'
                    }
                }
            },
            'client_config': CLIENT_CONFIG
        }

        _ctx = self.get_mock_ctx(
            'test_create',
            test_properties=node_properties,
            test_runtime_properties=RUNTIME_PROPERTIES,
            type_hierarchy=QUEUE_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('sqs')

        with patch('boto3.client', fake_boto):
            fake_client.create_queue = MagicMock(return_value={
                'QueueUrl': 'fake_QueueUrl'
            })

            fake_client.get_queue_attributes = MagicMock(return_value={
                'Attributes': {
                    'QueueArn': 'fake_QueueArn'
                }
            })
            queue.create(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('sqs', **CLIENT_CONFIG)

            fake_client.create_queue.assert_called_with(
                Attributes={
                    'Policy': POLICY_STRING,
                    'MessageRetentionPeriod': '86400',
                    'VisibilityTimeout': '180'
                },
                QueueName='test-queue'
            )

            fake_client.get_queue_attributes.assert_called_with(
                AttributeNames=['QueueArn'], QueueUrl='fake_QueueUrl'
            )

            self.assertEqual(
                _ctx.instance.runtime_properties,
                RUNTIME_PROPERTIES_AFTER_CREATE
            )

    def test_delete(self):
        _ctx = self.get_mock_ctx(
            'test_delete',
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES_AFTER_CREATE,
            type_hierarchy=QUEUE_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('sqs')

        with patch('boto3.client', fake_boto):
            fake_client.delete_queue = MagicMock(
                return_value=DELETE_RESPONSE
            )

            queue.delete(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('sqs', **CLIENT_CONFIG)

            fake_client.delete_queue.assert_called_with(
                QueueUrl='fake_QueueUrl'
            )

            self.assertEqual(
                _ctx.instance.runtime_properties,
                {
                    'aws_resource_arn': 'fake_QueueArn',
                    'aws_resource_id': 'fake_QueueUrl',
                    'resource_config': {}
                }
            )

    def test_SQSQueueClass_status(self):
        fake_boto, fake_client = self.fake_boto_client('sqs')
        with patch('boto3.client', fake_boto):
            test_instance = queue.SQSQueue("ctx_node", resource_id='queue_id',
                                           client=fake_client, logger=None)

            self.assertEqual(test_instance.status, None)

    def test_SQSQueueClass_properties(self):
        fake_boto, fake_client = self.fake_boto_client('sqs')
        with patch('boto3.client', fake_boto):
            test_instance = queue.SQSQueue("ctx_node", resource_id='queue_id',
                                           client=fake_client, logger=None)

            self.assertEqual(test_instance.properties, None)

            fake_client.list_queues.assert_called_with(
                QueueNamePrefix='queue_id'
            )

    def test_SQSQueueClass_properties_list_queue(self):
        fake_boto, fake_client = self.fake_boto_client('sqs')
        with patch('boto3.client', fake_boto):
            fake_client.list_queues = MagicMock(
                return_value={
                    'QueueUrls': ['c']
                }
            )

            test_instance = queue.SQSQueue("ctx_node", resource_id='queue_id',
                                           client=fake_client, logger=None)

            self.assertEqual(test_instance.properties, 'c')

            fake_client.list_queues.assert_called_with(
                QueueNamePrefix='queue_id'
            )


if __name__ == '__main__':
    unittest.main()
