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
from __future__ import unicode_literals

import unittest

from mock import patch, MagicMock

from cloudify_awssdk.common.tests.test_base import TestBase, mock_decorator
from cloudify_awssdk.ec2.resources.vpn_connection import EC2VPNConnection
from cloudify_awssdk.ec2.resources import vpn_connection
from cloudify_awssdk.common import constants


class TestEC2VPNConnection(TestBase):

    def setUp(self):
        super(TestEC2VPNConnection, self).setUp()
        self.vpn_connection = EC2VPNConnection("ctx_node", resource_id=True,
                                               client=True, logger=None)
        mock1 = patch('cloudify_awssdk.common.decorators.aws_resource',
                      mock_decorator)
        mock1.start()
        reload(vpn_connection)

    def test_class_properties(self):
        effect = self.get_client_error_exception(
            name=vpn_connection.RESOURCE_TYPE)

        self.vpn_connection.client = \
            self.make_client_function('describe_vpn_connections',
                                      side_effect=effect)
        self.assertIsNone(self.vpn_connection.properties)

        response = \
            {
                vpn_connection.VPN_CONNECTIONS: [
                    {
                        'CustomerGatewayConfiguration':
                            'customer_gateway_configuration_test',
                        'CustomerGatewayId': 'customer_gateway_id_test',
                        'Category': 'category_test',
                        'State': 'state_test',
                        'Type': 'type_test',
                        'VpnConnectionId': 'vpn_connection_id_test',
                        'VpnGatewayId': 'vpn_gateway_id_test',
                        'Options': {
                            'StaticRoutesOnly': True
                        },
                        'Routes': [
                            {
                                'DestinationCidrBlock':
                                    'destination_cidr_block_test',
                                'Source': 'source_test',
                                'State': 'state_test'
                            },
                        ],
                        'Tags': [
                            {
                                'Key': 'key_test',
                                'Value': 'value_test'
                            },
                        ],
                        'VgwTelemetry': [
                            {
                                'AcceptedRouteCount': 1,
                                'LastStatusChange': '2015/01/11',
                                'OutsideIpAddress': 'outside_ip_address_test',
                                'Status': 'status_test',
                                'StatusMessage': 'status_message_test'
                            },
                        ],
                    },
                ]
            }

        self.vpn_connection.describe_vpn_connection_filter = {
            vpn_connection.VPN_CONNECTION_IDS:
                ['vpn_connection_id_test']
        }
        self.vpn_connection.client = self.make_client_function(
            'describe_vpn_connections', return_value=response)

        self.assertEqual(
            self.vpn_connection.properties[
                vpn_connection.VPN_CONNECTION_ID],
            'vpn_connection_id_test'
        )

    def test_class_status(self):
        response = \
            {
                vpn_connection.VPN_CONNECTIONS: [
                    {
                        'CustomerGatewayConfiguration':
                            'customer_gateway_configuration_test',
                        'CustomerGatewayId': 'customer_gateway_id_test',
                        'Category': 'category_test',
                        'State': 'state_test',
                        'Type': 'type_test',
                        'VpnConnectionId': 'vpn_connection_id_test',
                        'VpnGatewayId': 'vpn_gateway_id_test',
                        'Options': {
                            'StaticRoutesOnly': True
                        },
                        'Routes': [
                            {
                                'DestinationCidrBlock':
                                    'destination_cidr_block_test',
                                'Source': 'source_test',
                                'State': 'state_test'
                            },
                        ],
                        'Tags': [
                            {
                                'Key': 'key_test',
                                'Value': 'value_test'
                            },
                        ],
                        'VgwTelemetry': [
                            {
                                'AcceptedRouteCount': 1,
                                'LastStatusChange': '2015/01/11',
                                'OutsideIpAddress': 'outside_ip_address_test',
                                'Status': 'status_test',
                                'StatusMessage': 'status_message_test'
                            },
                        ],
                    },
                ]
            }

        self.vpn_connection.client = self.make_client_function(
            'describe_vpn_connections', return_value=response)

        self.assertEqual(self.vpn_connection.status, 'state_test')

    def test_class_create(self):
        params = \
            {
                'CustomerGatewayId': 'customer_gateway_id_test',
                'Type': 'type_test',
                'VpnGatewayId': 'vpn_gateway_id_test',
                'DryRun': True,
                'PeerRegion': 'peer_region_test',
                'Options': {
                    'StaticRoutesOnly': True,
                    'TunnelOptions': [
                        {
                            'TunnelInsideCidr': 'tunnel_inside_cidr_test',
                            'PreSharedKey': 'pre_shared_key',
                        }
                    ]
                }
            }

        response = \
            {
                vpn_connection.VPN_CONNECTION:
                    {
                        'CustomerGatewayConfiguration':
                            'customer_gateway_configuration_test',
                        'CustomerGatewayId': 'customer_gateway_id_test',
                        'Category': 'category_test',
                        'State': 'state_test',
                        'Type': 'type_test',
                        'VpnConnectionId': 'vpn_connection_id_test',
                        'VpnGatewayId': 'vpn_gateway_id_test',
                        'Options': {
                            'StaticRoutesOnly': True
                        },
                        'Routes': [
                            {
                                'DestinationCidrBlock':
                                    'destination_cidr_block_test',
                                'Source': 'source_test',
                                'State': 'state_test'
                            },
                        ],
                        'Tags': [
                            {
                                'Key': 'key_test',
                                'Value': 'value_test'
                            },
                        ],
                        'VgwTelemetry': [
                            {
                                'AcceptedRouteCount': 1,
                                'LastStatusChange': '2015/01/11',
                                'OutsideIpAddress':
                                    'outside_ip_address_test',
                                'Status': 'status_test',
                                'StatusMessage': 'status_message_test'
                            },
                        ],
                    }
            }

        self.vpn_connection.client = self.make_client_function(
            'create_vpn_connection', return_value=response)

        self.assertEqual(self.vpn_connection.create(params), response)

    def test_class_delete(self):
        params = \
            {
                'DryRun': True,
                'VpnConnectionId': 'vpn_connection_id_test',
            }

        response = None

        self.vpn_connection.client = self.make_client_function(
            'delete_vpn_connection', return_value=response)
        self.assertEqual(self.vpn_connection.delete(params), None)

    def test_prepare(self):
        ctx = self.get_mock_ctx("EC2VPNConnection")
        vpn_connection.prepare(ctx, 'config')
        self.assertEqual(
            ctx.instance.runtime_properties['resource_config'],
            'config')

    def test_create(self):
        iface = MagicMock()
        ctx = self.get_mock_ctx("EC2VPNConnection")

        config = \
            {
                'CustomerGatewayId': 'customer_gateway_id_test',
                'Type': 'type_test',
                'VpnGatewayId': 'vpn_gateway_id_test',
                'DryRun': True,
                'PeerRegion': 'peer_region_test',
                'Options': {
                    'StaticRoutesOnly': True,
                    'TunnelOptions': [
                        {
                            'TunnelInsideCidr': 'tunnel_inside_cidr_test',
                            'PreSharedKey': 'pre_shared_key',
                        }
                    ]
                }
            }

        response = \
            {
                vpn_connection.VPN_CONNECTION:
                    {
                        'CustomerGatewayConfiguration':
                            'customer_gateway_configuration_test',
                        'CustomerGatewayId': 'customer_gateway_id_test',
                        'Category': 'category_test',
                        'State': 'state_test',
                        'Type': 'type_test',
                        'VpnConnectionId': 'vpn_connection_id_test',
                        'VpnGatewayId': 'vpn_gateway_id_test',
                        'Options': {
                            'StaticRoutesOnly': True
                        },

                        'Routes': [
                            {
                                'DestinationCidrBlock':
                                    'destination_cidr_block_test',
                                'Source': 'source_test',
                                'State': 'state_test'
                            },
                        ],
                        'Tags': [
                            {
                                'Key': 'key_test',
                                'Value': 'value_test'
                            },
                        ],
                        'VgwTelemetry': [
                            {
                                'AcceptedRouteCount': 1,
                                'LastStatusChange': '2015/01/11',
                                'OutsideIpAddress':
                                    'outside_ip_address_test',
                                'Status': 'status_test',
                                'StatusMessage': 'status_message_test'
                            },
                        ],
                    }
            }

        iface.create = self.mock_return(response)
        vpn_connection.create(ctx, iface, config)
        self.assertEqual(
            ctx.instance.runtime_properties[constants.EXTERNAL_RESOURCE_ID],
            'vpn_connection_id_test'
        )

    def test_delete(self):
        iface = MagicMock()
        ctx = self.get_mock_ctx("EC2VPNConnection")
        config = \
            {
                'CustomerGatewayId': 'customer_gateway_id_test',
                'Type': 'type_test',
                'VpnGatewayId': 'vpn_gateway_id_test',
                'DryRun': True,
                'PeerRegion': 'peer_region_test',
                'Options': {
                    'StaticRoutesOnly': True,
                    'TunnelOptions': [
                        {
                            'TunnelInsideCidr': 'tunnel_inside_cidr_test',
                            'PreSharedKey': 'pre_shared_key',
                        }
                    ]
                }
            }
        ctx.instance.runtime_properties['resource_config'] = config
        ctx.instance.runtime_properties[constants.EXTERNAL_RESOURCE_ID]\
            = 'vpn_connection_id_test'
        vpn_connection.delete(ctx, iface, {})
        self.assertTrue(iface.delete.called)


if __name__ == '__main__':
    unittest.main()
