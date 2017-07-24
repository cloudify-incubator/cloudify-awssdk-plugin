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
from cloudify_awssdk.common.tests.test_base import TestBase, mock_decorator
from cloudify_awssdk.s3.resources.bucket_policy import (S3BucketPolicy, BUCKET,
                                                        POLICY)
from mock import patch, MagicMock
from cloudify_awssdk.common.constants import EXTERNAL_RESOURCE_ID
from cloudify_awssdk.s3.resources import bucket_policy

PATCH_PREFIX = 'cloudify_awssdk.s3.resources.bucket_policy.'


class TestS3BacketPolicy(TestBase):

    def setUp(self):
        super(TestS3BacketPolicy, self).setUp()
        self.policy = S3BucketPolicy("ctx_node", resource_id=True,
                                     client=True, logger=None)
        mock1 = patch('cloudify_awssdk.common.decorators.aws_resource',
                      mock_decorator)
        mock1.start()
        reload(bucket_policy)

    def test_class_properties(self):
        effect = self.get_client_error_exception(name='S3 Bucket')
        self.policy.client = self.make_client_function('get_bucket_policy',
                                                       side_effect=effect)
        res = self.policy.properties
        self.assertIsNone(res)

        value = {'Policy': 'test_name'}
        self.policy.client = self.make_client_function('get_bucket_policy',
                                                       return_value=value)
        res = self.policy.properties
        self.assertEqual(res, 'test_name')

        self.policy.client = self.make_client_function('get_bucket_policy',
                                                       return_value={})
        res = self.policy.properties
        self.assertIsNone(res)

    def test_class_status(self):
        self.policy.client = self.make_client_function('get_bucket_policy',
                                                       return_value={})
        res = self.policy.status
        self.assertIsNone(res)

        value = {'Policy': {'Status': 'ok'}}
        self.policy.client = self.make_client_function('get_bucket_policy',
                                                       return_value=value)
        res = self.policy.status
        self.assertEqual(res, 'ok')

    def test_class_create(self):
        value = 'test'
        self.policy.client = self.make_client_function('put_bucket_policy',
                                                       return_value=value)
        res = self.policy.create({})
        self.assertEqual(res, 'test')

    def test_class_delete(self):
        params = {}
        self.policy.client = self.make_client_function('delete_bucket_policy')
        self.policy.delete(params)
        self.assertTrue(self.policy.client.delete_bucket_policy.called)

    def test_prepare(self):
        ctx = self.get_mock_ctx("Backet")
        bucket_policy.prepare(ctx, 'config')
        self.assertEqual(ctx.instance.runtime_properties['resource_config'],
                         'config')

    def test_create(self):
        ctx = self.get_mock_ctx("Backet")
        config = {BUCKET: 'bucket', POLICY: 'policy'}
        iface = MagicMock()
        iface.create = self.mock_return('location')
        bucket_policy.create(ctx, iface, config)
        self.assertEqual(ctx.instance.runtime_properties[POLICY],
                         'policy')

        config = {BUCKET: 'bucket', POLICY: ['policy']}
        iface = MagicMock()
        iface.create = self.mock_return('location')
        bucket_policy.create(ctx, iface, config)
        self.assertEqual(ctx.instance.runtime_properties[POLICY],
                         '["policy"]')

        config = {POLICY: 'policy'}
        ctx_target = self.get_mock_relationship_ctx(
            "bucket",
            test_target=self.get_mock_ctx("Backet",
                                          {},
                                          {EXTERNAL_RESOURCE_ID: 'ext_id'}))
        iface = MagicMock()
        iface.create = self.mock_return('location')
        with patch(PATCH_PREFIX + 'utils') as utils:
            utils.find_rel_by_node_type = self.mock_return(ctx_target)
            bucket_policy.create(ctx, iface, config)
            self.assertEqual(ctx.instance.runtime_properties[BUCKET],
                             'ext_id')
            self.assertEqual(ctx.instance.runtime_properties[POLICY],
                             'policy')

    def test_delete(self):
        iface = MagicMock()
        bucket_policy.delete(iface, {})
        self.assertTrue(iface.delete.called)


if __name__ == '__main__':
    unittest.main()
