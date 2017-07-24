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
from cloudify_awssdk.ec2.resources.vpc import EC2Vpc, VPC, CIDR_BLOCK, VPC_ID
from mock import patch, MagicMock
from cloudify_awssdk.ec2.resources import vpc


class TestEC2Vpc(TestBase):

    def setUp(self):
        super(TestEC2Vpc, self).setUp()
        self.vpc = EC2Vpc("ctx_node", resource_id=True,
                          client=True, logger=None)
        mock1 = patch('cloudify_awssdk.common.decorators.aws_resource',
                      mock_decorator)
        mock2 = patch('cloudify_awssdk.common.decorators.wait_for_status',
                      mock_decorator)
        mock1.start()
        mock2.start()
        reload(vpc)

    def test_class_properties(self):
        effect = self.get_client_error_exception(name='EC2 Vpc')
        self.vpc.client = self.make_client_function('describe_vpcs',
                                                    side_effect=effect)
        res = self.vpc.properties
        self.assertIsNone(res)

        value = {}
        self.vpc.client = self.make_client_function('describe_vpcs',
                                                    return_value=value)
        res = self.vpc.properties
        self.assertIsNone(res)

        value = {'Vpcs': [{VPC_ID: 'test_name'}]}
        self.vpc.client = self.make_client_function('describe_vpcs',
                                                    return_value=value)
        res = self.vpc.properties
        self.assertEqual(res[VPC_ID], 'test_name')

    def test_class_status(self):
        value = {}
        self.vpc.client = self.make_client_function('describe_vpcs',
                                                    return_value=value)
        res = self.vpc.status
        self.assertIsNone(res)

        value = {'Vpcs': [{VPC_ID: 'test_name', 'State': 'available'}]}
        self.vpc.client = self.make_client_function('describe_vpcs',
                                                    return_value=value)
        res = self.vpc.status
        self.assertEqual(res, 'available')

    def test_class_create(self):
        value = {VPC: 'test'}
        self.vpc.client = self.make_client_function('create_vpc',
                                                    return_value=value)
        res = self.vpc.create(value)
        self.assertEqual(res, value[VPC])

    def test_class_delete(self):
        params = {}
        self.vpc.client = self.make_client_function('delete_vpc')
        self.vpc.delete(params)
        self.assertTrue(self.vpc.client.delete_vpc.called)

        params = {VPC: 'vpc', CIDR_BLOCK: 'cidr_block'}
        self.vpc.delete(params)
        self.assertEqual(params[CIDR_BLOCK], 'cidr_block')

    def test_prepare(self):
        ctx = self.get_mock_ctx("Vpc")
        config = {VPC_ID: 'vpc', CIDR_BLOCK: 'cidr_block'}
        iface = MagicMock()
        iface.create = self.mock_return(config)
        vpc.prepare(ctx, iface, config)
        self.assertEqual(ctx.instance.runtime_properties['resource_config'],
                         config)

    def test_create(self):
        ctx = self.get_mock_ctx("Vpc")
        config = {VPC_ID: 'vpc', CIDR_BLOCK: 'cidr_block'}
        self.vpc.resource_id = config[VPC_ID]
        iface = MagicMock()
        iface.create = self.mock_return(config)
        vpc.create(ctx, iface, config)
        self.assertEqual(self.vpc.resource_id,
                         'vpc')

    def test_delete(self):
        iface = MagicMock()
        vpc.delete(iface, {})
        self.assertTrue(iface.delete.called)


if __name__ == '__main__':
    unittest.main()
