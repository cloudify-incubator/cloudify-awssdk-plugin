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
from cloudify_boto3.common.tests.test_base import TestBase, mock_decorator
from cloudify_boto3.s3.resources.bucket import S3Bucket, BUCKET, LOCATION
from mock import patch, MagicMock
from cloudify_boto3.s3.resources import bucket


class TestS3Backet(TestBase):

    def setUp(self):
        self.bucket = S3Bucket("ctx_node", resource_id=True,
                               client=True, logger=None)
        mock1 = patch('cloudify_boto3.common.decorators.aws_resource',
                      mock_decorator)
        mock1.start()
        reload(bucket)

    def test_class_properties(self):
        effect = self.get_client_error_exception(name='S3 Bucket')
        self.bucket.client = self.make_client_function('list_buckets',
                                                       side_effect=effect)
        res = self.bucket.properties
        self.assertIsNone(res)

        value = [{'Name': 'test_name'}]
        self.bucket.client = self.make_client_function('list_buckets',
                                                       return_value=value)
        res = self.bucket.properties
        self.assertIsNone(res)

        self.bucket.resource_id = 'test_name'
        res = self.bucket.properties
        self.assertEqual(res['Name'], 'test_name')

    def test_class_status(self):
        value = [{'Name': 'test_name', 'Status': 'ok'}]
        self.bucket.client = self.make_client_function('list_buckets',
                                                       return_value=value)
        res = self.bucket.status
        self.assertIsNone(res)

        self.bucket.resource_id = 'test_name'
        res = self.bucket.status
        self.assertEqual(res, 'ok')

    def test_class_create(self):
        value = {'Location': 'test'}
        self.bucket.client = self.make_client_function('create_bucket',
                                                       return_value=value)
        res = self.bucket.create(value)
        self.assertEqual(res, value)

    def test_class_delete(self):
        params = {}
        self.bucket.client = self.make_client_function('delete_bucket')
        self.bucket.delete(params)
        self.assertTrue(self.bucket.client.delete_bucket.called)

        params = {BUCKET: 'bucket', LOCATION: 'location'}
        self.bucket.delete(params)
        self.assertEqual(params[LOCATION], 'location')

    def test_prepare(self):
        ctx = self.get_mock_ctx("Backet")
        bucket.prepare(ctx, 'config')
        self.assertEqual(ctx.instance.runtime_properties['resource_config'],
                         'config')

    def test_create(self):
        ctx = self.get_mock_ctx("Backet")
        config = {BUCKET: 'bucket'}
        iface = MagicMock()
        iface.create = self.mock_return({LOCATION: 'location'})
        bucket.create(ctx, iface, config)
        self.assertEqual(ctx.instance.runtime_properties[LOCATION],
                         'location')

    def test_delete(self):
        iface = MagicMock()
        bucket.delete(iface, {})
        self.assertTrue(iface.delete.called)


if __name__ == '__main__':
    unittest.main()
