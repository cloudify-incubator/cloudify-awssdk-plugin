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
from cloudify_awssdk.ec2.resources.instances import (
    EC2Instances, INSTANCES, RESERVATIONS, INSTANCE_ID)
from mock import patch, MagicMock
from cloudify_awssdk.ec2.resources import instances
from cloudify.state import current_ctx


class TestEC2Instances(TestBase):

    def setUp(self):
        self.instances = EC2Instances("ctx_node", resource_id=True,
                                      client=True, logger=None)
        mock1 = patch('cloudify_awssdk.common.decorators.aws_resource',
                      mock_decorator)
        mock2 = patch('cloudify_awssdk.common.decorators.wait_for_status',
                      mock_decorator)
        mock1.start()
        mock2.start()
        reload(instances)

    def test_class_properties(self):
        effect = self.get_client_error_exception(name='EC2 Instances')
        self.instances.client = \
            self.make_client_function('describe_instances',
                                      side_effect=effect)
        res = self.instances.properties
        self.assertIsNone(res)

        value = {}
        self.instances.client = \
            self.make_client_function('describe_instances',
                                      return_value=value)
        res = self.instances.properties
        self.assertIsNone(res)

        value = {RESERVATIONS: [{INSTANCES: [{INSTANCE_ID: 'test_name'}]}]}
        self.instances.client = \
            self.make_client_function('describe_instances',
                                      return_value=value)
        res = self.instances.properties
        self.assertEqual(res[INSTANCE_ID], 'test_name')

    def test_class_status(self):
        value = {}
        self.instances.client = \
            self.make_client_function('describe_instances',
                                      return_value=value)
        res = self.instances.status
        self.assertIsNone(res)

        value = {RESERVATIONS: [{INSTANCES: [{
            INSTANCE_ID: 'test_name', 'State': {'Code': 16}}]}]}
        self.instances.client = \
            self.make_client_function('describe_instances',
                                      return_value=value)
        res = self.instances.status
        self.assertEqual(res, 16)

    def test_class_create(self):
        value = {RESERVATIONS: [{INSTANCES: [{INSTANCE_ID: 'test_name'}]}]}
        self.instances.client = \
            self.make_client_function('run_instances',
                                      return_value=value)
        res = self.instances.create(value)
        self.assertEqual(res, value)

    def test_class_delete(self):
        params = {INSTANCE_ID: 'test_name'}
        self.instances.client = \
            self.make_client_function('terminate_instances')
        self.instances.delete(params)
        self.assertTrue(self.instances.client.terminate_instances
                        .called)

        params = {INSTANCE_ID: 'test_name'}
        self.instances.delete(params)
        self.assertEqual(params[INSTANCE_ID], 'test_name')

    def test_prepare(self):
        ctx = self.get_mock_ctx(
            "EC2Instances",
            type_hierarchy=['cloudify.nodes.Root', 'cloudify.nodes.Compute'])
        params = {'ImageId': 'test image', 'InstanceType': 'test type'}
        instances.prepare(ctx, EC2Instances, params)
        self.assertEqual(ctx.instance.runtime_properties['resource_config'],
                         params)

    def test_create(self):
        ctx = self.get_mock_ctx(
            "EC2Instances",
            test_properties={'os_family': 'linux'},
            type_hierarchy=['cloudify.nodes.Root', 'cloudify.nodes.Compute'])
        current_ctx.set(ctx=ctx)
        params = {'ImageId': 'test image', 'InstanceType': 'test type'}
        self.instances.resource_id = 'test_name'
        iface = MagicMock()
        value = {INSTANCES: [{INSTANCE_ID: 'test_name'}]}
        iface.create = self.mock_return(value)
        instances.create(ctx, iface, params)
        self.assertEqual(self.instances.resource_id,
                         'test_name')

    def test_create_with_relationships(self):
        ctx = self.get_mock_ctx(
            "EC2Instances",
            test_properties={'os_family': 'linux'},
            type_hierarchy=['cloudify.nodes.Root', 'cloudify.nodes.Compute'])
        current_ctx.set(ctx=ctx)
        params = {'ImageId': 'test image', 'InstanceType': 'test type'}
        self.instances.resource_id = 'test_name'
        iface = MagicMock()
        with patch('cloudify_awssdk.common.utils.find_rel_by_node_type'):
            instances.create(ctx, iface, params)
            self.assertEqual(self.instances.resource_id,
                             'test_name')

    def test_delete(self):
        ctx = self.get_mock_ctx(
            "EC2Instances",
            test_properties={'os_family': 'linux'},
            type_hierarchy=['cloudify.nodes.Root', 'cloudify.nodes.Compute'])
        current_ctx.set(ctx=ctx)
        iface = MagicMock()
        instances.delete(iface, {})
        self.assertTrue(iface.delete.called)


if __name__ == '__main__':
    unittest.main()
