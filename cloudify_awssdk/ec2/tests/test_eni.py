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
from cloudify_awssdk.ec2.resources.eni import EC2NetworkInterface, \
    NETWORKINTERFACES, NETWORKINTERFACE_ID, SUBNET_ID, \
    SUBNET_TYPE, INSTANCE_TYPE_DEPRECATED, ATTACHMENT_ID
from mock import patch, MagicMock
from cloudify_awssdk.ec2.resources import eni


class TestEC2NetworkInterface(TestBase):

    def setUp(self):
        self.eni = EC2NetworkInterface("ctx_node", resource_id=True,
                                       client=True, logger=None)
        mock1 = patch('cloudify_awssdk.common.decorators.aws_resource',
                      mock_decorator)
        mock2 = patch('cloudify_awssdk.common.decorators.wait_for_status',
                      mock_decorator)
        mock1.start()
        mock2.start()
        reload(eni)

    def test_class_properties(self):
        effect = self.get_client_error_exception(name='EC2 Network Interface')
        self.eni.client = \
            self.make_client_function('describe_network_interfaces',
                                      side_effect=effect)
        res = self.eni.properties
        self.assertIsNone(res)

        value = {}
        self.eni.client = \
            self.make_client_function('describe_network_interfaces',
                                      return_value=value)
        res = self.eni.properties
        self.assertIsNone(res)

        value = {NETWORKINTERFACES: [{NETWORKINTERFACE_ID: 'test_name'}]}
        self.eni.client = \
            self.make_client_function('describe_network_interfaces',
                                      return_value=value)
        res = self.eni.properties
        self.assertEqual(res[NETWORKINTERFACE_ID], 'test_name')

    def test_class_status(self):
        value = {}
        self.eni.client = \
            self.make_client_function('describe_network_interfaces',
                                      return_value=value)
        res = self.eni.status
        self.assertIsNone(res)

        value = {NETWORKINTERFACES: [{NETWORKINTERFACE_ID: 'test_name',
                                      'Status': 'available'}]}
        self.eni.client = \
            self.make_client_function('describe_network_interfaces',
                                      return_value=value)
        res = self.eni.status
        self.assertEqual(res, 'available')

    def test_class_create(self):
        value = {'NetworkInterface': 'test'}
        self.eni.client = \
            self.make_client_function('create_network_interface',
                                      return_value=value)
        res = self.eni.create(value)
        self.assertEqual(res, value['NetworkInterface'])

    def test_class_delete(self):
        params = {}
        self.eni.client = \
            self.make_client_function('delete_network_interface')
        self.eni.delete(params)
        self.assertTrue(self.eni.client.delete_network_interface
                        .called)

        params = {'NetworkInterface': 'network interface'}
        self.eni.delete(params)
        self.assertEqual(params['NetworkInterface'], 'network interface')

    def test_class_attach(self):
        value = {ATTACHMENT_ID: 'eni-attach'}
        self.eni.client = \
            self.make_client_function('attach_network_interface',
                                      return_value=value)
        with patch('cloudify_awssdk.ec2.resources.eni'
                   '.EC2NetworkInterface.attach'):
            res = self.eni.attach(value)
            self.assertEqual(res[ATTACHMENT_ID], value[ATTACHMENT_ID])

    def test_class_detach(self):
        params = {}
        self.eni.client = \
            self.make_client_function('detach_network_interface')
        self.eni.detach(params)
        self.assertTrue(self.eni.client.detach_network_interface
                        .called)
        params = {ATTACHMENT_ID: 'eni-attach'}
        self.eni.delete(params)
        self.assertTrue(self.eni.client.detach_network_interface
                        .called)

    def test_prepare(self):
        ctx = self.get_mock_ctx("NetworkInterface")
        config = {NETWORKINTERFACE_ID: 'eni'}
        eni.prepare(ctx, config)
        self.assertEqual(ctx.instance.runtime_properties['resource_config'],
                         config)

    def test_create(self):
        ctx = self.get_mock_ctx("NetworkInterface")
        config = {NETWORKINTERFACE_ID: 'eni', SUBNET_ID: 'subnet'}
        self.eni.resource_id = config[NETWORKINTERFACE_ID]
        iface = MagicMock()
        iface.create = self.mock_return(config)
        eni.create(ctx, iface, config)
        self.assertEqual(self.eni.resource_id,
                         'eni')

    def test_create_with_relationships(self):
        ctx = self.get_mock_ctx("NetworkInterface",
                                type_hierarchy=[SUBNET_TYPE])
        config = {NETWORKINTERFACE_ID: 'eni'}
        self.eni.resource_id = config[NETWORKINTERFACE_ID]
        iface = MagicMock()
        iface.create = self.mock_return(config)
        with patch('cloudify_awssdk.common.utils.find_rel_by_node_type'):
            eni.create(ctx, iface, config)
            self.assertEqual(self.eni.resource_id,
                             'eni')

    def test_attach(self):
        ctx = self.get_mock_ctx("NetworkInterface")
        self.eni.resource_id = 'eni'
        config = {ATTACHMENT_ID: 'eni-attach'}
        iface = MagicMock()
        iface.attach = self.mock_return(config)
        eni.attach(ctx, iface, config)
        self.assertEqual(self.eni.resource_id,
                         'eni')

    def test_attach_with_relationships(self):
        ctx = self.get_mock_ctx("NetworkInterface",
                                type_hierarchy=[INSTANCE_TYPE_DEPRECATED])
        config = {ATTACHMENT_ID: 'eni-attach'}
        self.eni.resource_id = 'eni'
        iface = MagicMock()
        iface.attach = self.mock_return(config)
        with patch('cloudify_awssdk.common.utils.find_rel_by_node_type'):
            eni.attach(ctx, iface, config)
            self.assertEqual(self.eni.resource_id,
                             'eni')

    def test_delete(self):
        ctx = self.get_mock_ctx("NetworkInterface")
        iface = MagicMock()
        eni.delete(ctx, iface, {})
        self.assertTrue(iface.delete.called)

    def test_detach(self):
        ctx = self.get_mock_ctx("NetworkInterface")
        self.eni.resource_id = 'eni'
        config = {ATTACHMENT_ID: 'eni-attach'}
        iface = MagicMock()
        iface.detach = self.mock_return(config)
        eni.detach(ctx, iface, config)
        self.assertEqual(self.eni.resource_id,
                         'eni')

    def test_detach_with_relationships(self):
        ctx = self.get_mock_ctx("NetworkInterface",
                                type_hierarchy=[INSTANCE_TYPE_DEPRECATED])
        config = {NETWORKINTERFACE_ID: 'eni'}
        self.eni.resource_id = config[NETWORKINTERFACE_ID]
        iface = MagicMock()
        iface.detach = self.mock_return(config)
        ctx.instance.runtime_properties['attachment_id'] = 'eni-attach'
        eni.detach(ctx, iface, config)
        self.assertEqual(self.eni.resource_id,
                         'eni')


if __name__ == '__main__':
    unittest.main()
