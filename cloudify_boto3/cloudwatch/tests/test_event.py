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
import unittest
from mock import patch, MagicMock

from cloudify.state import current_ctx

from cloudify_boto3.common.tests.test_base import TestBase, CLIENT_CONFIG
from cloudify_boto3.common.tests.test_base import DEFAULT_RUNTIME_PROPERTIES
from cloudify_boto3.cloudwatch.resources import event


# Constants
EVENT_TH = ['cloudify.nodes.Root',
            'cloudify.nodes.aws.cloudwatch.Event']


class TestCloudwatchEvent(TestBase):

    def test_prepare(self):
        self._prepare_check(
            type_hierarchy=EVENT_TH,
            type_name='events',
            type_class=event
        )

    def test_create_raises_UnknownServiceError(self):
        self._prepare_create_raises_UnknownServiceError(
            type_hierarchy=EVENT_TH,
            type_name='events',
            type_class=event
        )

    def test_create(self):
        _ctx = self.get_mock_ctx(
            'test_create',
            test_properties={
                'use_external_resource': False,
                'resource_config': {
                    'a': 'b'
                },
                'client_config': CLIENT_CONFIG
            },
            test_runtime_properties=DEFAULT_RUNTIME_PROPERTIES,
            type_hierarchy=EVENT_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('events')

        with patch('boto3.client', fake_boto):
            fake_client.put_events = MagicMock(return_value={
                'event': 'message'
            })

            event.create(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('events', **CLIENT_CONFIG)

            fake_client.put_events.assert_called_with(a='b')

            self.assertEqual(
                _ctx.instance.runtime_properties,
                DEFAULT_RUNTIME_PROPERTIES
            )

    def test_CloudwatchEvent_status(self):
        fake_boto, fake_client = self.fake_boto_client('events')
        with patch('boto3.client', fake_boto):

            test_instance = event.CloudwatchEvent("ctx_node",
                                                  resource_id='user_id',
                                                  client=fake_client,
                                                  logger=None)

            self.assertEqual(test_instance.status, None)

    def test_CloudwatchEvent_properties(self):
        fake_boto, fake_client = self.fake_boto_client('events')
        with patch('boto3.client', fake_boto):

            test_instance = event.CloudwatchEvent("ctx_node",
                                                  resource_id='user_id',
                                                  client=fake_client,
                                                  logger=None)

            self.assertEqual(test_instance.properties, None)

    def test_CloudwatchEvent_delete(self):
        fake_boto, fake_client = self.fake_boto_client('events')
        with patch('boto3.client', fake_boto):

            test_instance = event.CloudwatchEvent("ctx_node",
                                                  resource_id='user_id',
                                                  client=fake_client,
                                                  logger=None)

            self.assertEqual(test_instance.delete(), None)


if __name__ == '__main__':
    unittest.main()
