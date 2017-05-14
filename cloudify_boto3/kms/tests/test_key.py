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
from cloudify_boto3.common.tests.test_base import CLIENT_CONFIG
from cloudify_boto3.kms.tests.test_kms import TestKMS
from cloudify_boto3.kms.resources import key


# Constants
KEY_TH = ['cloudify.nodes.Root',
          'cloudify.nodes.aws.kms.CustomerMasterKey']

NODE_PROPERTIES = {
    'use_external_resource': False,
    'resource_config': {
        "kwargs": {
            "Description": "An example CMK.",
            "Tags": [{
                "TagKey": "Cloudify",
                "TagValue": "Example"
            }]
        }
    },
    'client_config': CLIENT_CONFIG
}

RUNTIME_PROPERTIES = {
    'resource_config': {}
}

RUNTIME_PROPERTIES_AFTER_CREATE = {
    'aws_resource_arn': 'arn_id',
    'aws_resource_id': 'key_id',
    'resource_config': {}
}


class TestKMSKey(TestKMS):

    def test_prepare(self):
        _ctx = self.get_mock_ctx(
            'test_prepare',
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES,
            type_hierarchy=KEY_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('kms')

        with patch('boto3.client', fake_boto):
            key.prepare(ctx=_ctx, resource_config=None, iface=None)
            self.assertEqual(
                _ctx.instance.runtime_properties, {
                    'resource_config': {
                        'Tags': [{
                            'TagValue': 'Example',
                            'TagKey': 'Cloudify'
                        }],
                        'Description': 'An example CMK.'
                    }
                }
            )

    def test_create_raises_UnknownServiceError(self):
        _ctx, fake_boto, fake_client = self._prepare_context(KEY_TH)

        with patch('boto3.client', fake_boto):
            with self.assertRaises(UnknownServiceError) as error:
                key.create(ctx=_ctx, resource_config=None, iface=None)

            self.assertEqual(
                str(error.exception),
                "Unknown service: 'kms'. Valid service names are: ['rds']"
            )

            fake_boto.assert_called_with('kms', **CLIENT_CONFIG)

    def test_create(self):
        _ctx, fake_boto, fake_client = self._prepare_context(
            KEY_TH, NODE_PROPERTIES
        )

        with patch('boto3.client', fake_boto):
            fake_client.create_key = MagicMock(return_value={
                'KeyMetadata': {
                    'Arn': "arn_id",
                    'KeyId': 'key_id'
                }
            })

            key.create(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('kms', **CLIENT_CONFIG)

            fake_client.create_key.assert_called_with(
                Description='An example CMK.',
                Tags=[{'TagKey': 'Cloudify', 'TagValue': 'Example'}]
            )

            self.assertEqual(
                _ctx.instance.runtime_properties,
                RUNTIME_PROPERTIES_AFTER_CREATE
            )

    def test_enable(self):
        _ctx, fake_boto, fake_client = self._prepare_context(
            KEY_TH, NODE_PROPERTIES, RUNTIME_PROPERTIES_AFTER_CREATE
        )

        with patch('boto3.client', fake_boto):
            fake_client.schedule_key_deletion = MagicMock(return_value={})

            key.enable(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('kms', **CLIENT_CONFIG)

            self.assertEqual(
                _ctx.instance.runtime_properties,
                RUNTIME_PROPERTIES_AFTER_CREATE
            )

    def test_disable(self):
        _ctx, fake_boto, fake_client = self._prepare_context(
            KEY_TH, NODE_PROPERTIES, RUNTIME_PROPERTIES_AFTER_CREATE
        )

        with patch('boto3.client', fake_boto):
            fake_client.schedule_key_deletion = MagicMock(return_value={})

            key.disable(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('kms', **CLIENT_CONFIG)

            self.assertEqual(
                _ctx.instance.runtime_properties,
                RUNTIME_PROPERTIES_AFTER_CREATE
            )

    def test_delete(self):
        _ctx, fake_boto, fake_client = self._prepare_context(
            KEY_TH, NODE_PROPERTIES, RUNTIME_PROPERTIES_AFTER_CREATE
        )

        with patch('boto3.client', fake_boto):
            fake_client.schedule_key_deletion = MagicMock(return_value={})

            key.delete(ctx=_ctx, resource_config=None, iface=None)

            fake_boto.assert_called_with('kms', **CLIENT_CONFIG)

            fake_client.schedule_key_deletion.assert_called_with(
                KeyId='key_id'
            )

            self.assertEqual(
                _ctx.instance.runtime_properties,
                RUNTIME_PROPERTIES_AFTER_CREATE
            )

    def test_KMSKey_status(self):
        fake_boto, fake_client = self.fake_boto_client('kms')

        test_instance = key.KMSKey("ctx_node", resource_id='queue_id',
                                   client=fake_client, logger=None)

        self.assertEqual(test_instance.status, None)

    def test_KMSKey_properties(self):
        fake_boto, fake_client = self.fake_boto_client('kms')

        test_instance = key.KMSKey("ctx_node", resource_id='queue_id',
                                   client=fake_client, logger=None)

        self.assertEqual(test_instance.properties, None)

    def test_KMSKey_properties_with_key(self):
        fake_boto, fake_client = self.fake_boto_client('kms')

        test_instance = key.KMSKey("ctx_node", resource_id='queue_id',
                                   client=fake_client, logger=None)

        fake_client.describe_key = MagicMock(
            return_value={'KeyMetadata': 'z'}
        )

        self.assertEqual(test_instance.properties, 'z')

    def test_KMSKey_enable(self):
        fake_boto, fake_client = self.fake_boto_client('kms')

        test_instance = key.KMSKey("ctx_node", resource_id='queue_id',
                                   client=fake_client, logger=None)

        fake_client.enable_key = MagicMock(
            return_value={'KeyMetadata': 'y'}
        )

        self.assertEqual(
            test_instance.enable({'a': 'b'}),
            {'KeyMetadata': 'y'}
        )

        fake_client.enable_key.assert_called_with(a='b')

    def test_KMSKey_disable(self):
        fake_boto, fake_client = self.fake_boto_client('kms')

        test_instance = key.KMSKey("ctx_node", resource_id='queue_id',
                                   client=fake_client, logger=None)

        fake_client.disable_key = MagicMock(
            return_value={'KeyMetadata': 'y'}
        )

        self.assertEqual(
            test_instance.disable({'a': 'b'}),
            {'KeyMetadata': 'y'}
        )

        fake_client.disable_key.assert_called_with(a='b')


if __name__ == '__main__':
    unittest.main()
