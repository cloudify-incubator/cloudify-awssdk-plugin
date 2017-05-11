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
import copy
from cloudify_boto3.common.tests.test_base import TestBase, CLIENT_CONFIG
from mock import patch, MagicMock

from cloudify_boto3.common.connection import Boto3Connection


class TestConnection(TestBase):

    def test_client_direct_params(self):

        node = MagicMock()
        node.properties = {}

        fake_boto, fake_client = self.fake_boto_client('rds')
        with patch('boto3.client', fake_boto):
            connection = Boto3Connection(node, copy.deepcopy(CLIENT_CONFIG))
            connection.client('abc')

            fake_boto.assert_called_with(
                'abc', **CLIENT_CONFIG
            )

    def test_client_node_params(self):

        node = MagicMock()
        node.properties = {
            'client_config': copy.deepcopy(CLIENT_CONFIG)
        }

        fake_boto, fake_client = self.fake_boto_client('rds')
        with patch('boto3.client', fake_boto):
            connection = Boto3Connection(node, {'a': 'b'})
            connection.client('abc')

            fake_boto.assert_called_with(
                'abc', **CLIENT_CONFIG
            )

            self.assertEqual(connection.aws_config, CLIENT_CONFIG)


if __name__ == '__main__':
    unittest.main()
