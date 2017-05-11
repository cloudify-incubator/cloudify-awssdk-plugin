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

from cloudify_boto3.rds.resources import instance_read_replica
from botocore.exceptions import UnknownServiceError

from cloudify.exceptions import NonRecoverableError

from mock import patch, MagicMock
import unittest

from cloudify.state import current_ctx

from cloudify_boto3.common.tests.test_base import TestBase, CLIENT_CONFIG
from cloudify_boto3.common.tests.test_base import DELETE_RESPONSE

# Constants
INSTANCE_READ_REPLICA_TH = ['cloudify.nodes.Root',
                            'cloudify.nodes.aws.rds.InstanceReadReplica']

NODE_PROPERTIES = {
    'use_external_resource': False,
    'resource_id': 'devdbinstance-replica',
    'resource_config': {
        'kwargs': {
            'DBInstanceClass': 'db.t2.small',
            'AvailabilityZone': 'us-east-1d'
        }
    },
    'client_config': CLIENT_CONFIG
}

RUNTIME_PROPERTIES = {
    'resource_config': {
        'DBInstanceClass': 'db.t2.small',
        'AvailabilityZone': 'us-east-1d'
    }
}

RUNTIME_PROPERTIES_AFTER_CREATE = {
    'aws_resource_arn': 'DBInstanceArn',
    'aws_resource_id': 'devdbinstance',
    'resource_config': {
        'DBInstanceClass': 'db.t2.small',
        'AvailabilityZone': 'us-east-1d',
        'DBInstanceIdentifier': 'devdbinstance-replica'
    }
}


class TestRDSInstanceReadReplica(TestBase):

    def test_create_raises_UnknownServiceError(self):
        _test_name = 'test_create_UnknownServiceError'
        _test_runtime_properties = {
            'resource_config': {}
        }
        _ctx = self.get_mock_ctx(
            _test_name,
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=_test_runtime_properties,
            type_hierarchy=INSTANCE_READ_REPLICA_TH
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')
        with patch('boto3.client', fake_boto):
            with self.assertRaises(UnknownServiceError) as error:
                instance_read_replica.create(
                    ctx=_ctx, resource_config=None, iface=None
                )

            self.assertEqual(
                str(error.exception),
                "Unknown service: 'rds'. Valid service names are: ['rds']"
            )

            fake_boto.assert_called_with('rds', **CLIENT_CONFIG)

    def test_create(self):
        _test_name = 'test_create'
        _ctx = self.get_mock_ctx(
            _test_name,
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES,
            type_hierarchy=INSTANCE_READ_REPLICA_TH
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')
        with patch('boto3.client', fake_boto):

            fake_client.create_db_instance_read_replica = MagicMock(
                return_value={
                    'DBInstance': {
                        'DBInstanceIdentifier': 'devdbinstance',
                        'DBInstanceArn': 'DBInstanceArn'
                    }
                }
            )

            fake_client.describe_db_instances = MagicMock(return_value={
                'DBInstances': [{
                    'DBInstanceStatus': 'available'
                }]
            })

            instance_read_replica.create(
                ctx=_ctx, resource_config=None, iface=None
            )

            fake_boto.assert_called_with(
                'rds', **CLIENT_CONFIG
            )
            fake_client.create_db_instance_read_replica.assert_called_with(
                AvailabilityZone='us-east-1d', DBInstanceClass='db.t2.small',
                DBInstanceIdentifier='devdbinstance-replica'
            )
            fake_client.describe_db_instances.assert_called_with(
                DBInstanceIdentifier='devdbinstance'
            )

            self.assertEqual(
                _ctx.instance.runtime_properties,
                RUNTIME_PROPERTIES_AFTER_CREATE
            )

    def test_prepare(self):
        _ctx = self.get_mock_ctx(
            'test_prepare',
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES,
            type_hierarchy=INSTANCE_READ_REPLICA_TH
        )

        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')

        with patch('boto3.client', fake_boto):
            instance_read_replica.prepare(
                ctx=_ctx, resource_config=None, iface=None
            )
            self.assertEqual(
                _ctx.instance.runtime_properties, {
                    'resource_config': {
                        'DBInstanceClass': 'db.t2.small',
                        'AvailabilityZone': 'us-east-1d'
                    }
                }
            )

    def test_delete(self):
        _test_name = 'test_delete'
        _ctx = self.get_mock_ctx(
            _test_name,
            test_properties=NODE_PROPERTIES,
            test_runtime_properties=RUNTIME_PROPERTIES_AFTER_CREATE,
            type_hierarchy=INSTANCE_READ_REPLICA_TH
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')
        with patch('boto3.client', fake_boto):

            fake_client.delete_db_instance = MagicMock(
                return_value=DELETE_RESPONSE
            )

            instance_read_replica.delete(
                ctx=_ctx, resource_config=None, iface=None
            )

            fake_boto.assert_called_with(
                'rds', **CLIENT_CONFIG
            )
            fake_client.delete_db_instance.assert_called_with(
                DBInstanceIdentifier='devdbinstance', SkipFinalSnapshot=True
            )

            fake_client.describe_db_instances.assert_called_with(
                DBInstanceIdentifier='devdbinstance'
            )

            self.assertEqual(
                _ctx.instance.runtime_properties, {
                    'aws_resource_id': 'devdbinstance',
                    '__deleted': True,
                    'resource_config': {
                        'AvailabilityZone': 'us-east-1d',
                        'DBInstanceClass': 'db.t2.small',
                        'DBInstanceIdentifier': 'devdbinstance-replica'
                    },
                    'aws_resource_arn': 'DBInstanceArn'
                }
            )

    def _create_instance_relationships(self, node_id, type_hierarchy):
        _source_ctx = self.get_mock_ctx(
            'test_attach_source',
            test_properties={},
            test_runtime_properties={
                'resource_id': 'prepare_attach_source',
                'aws_resource_id': 'aws_resource_mock_id',
                '_set_changed': True,
                'resource_config': {}
            },
            type_hierarchy=INSTANCE_READ_REPLICA_TH
        )

        _target_ctx = self.get_mock_ctx(
            'test_attach_target',
            test_properties={},
            test_runtime_properties={
                'resource_id': 'prepare_attach_target',
                'aws_resource_id': 'aws_target_mock_id',
            },
            type_hierarchy=type_hierarchy
        )

        _ctx = self.get_mock_relationship_ctx(
            node_id,
            test_properties={},
            test_runtime_properties={},
            test_source=_source_ctx,
            test_target=_target_ctx,
            type_hierarchy=['cloudify.nodes.Root']
        )

        return _source_ctx, _target_ctx, _ctx

    def test_prepare_assoc_SubnetGroup(self):
        _source_ctx, _target_ctx, _ctx = self._create_instance_relationships(
            'test_prepare_assoc',
            ['cloudify.nodes.Root', 'cloudify.nodes.aws.rds.SubnetGroup']
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')

        with patch('boto3.client', fake_boto):
            instance_read_replica.prepare_assoc(
                ctx=_ctx, resource_config=None, iface=None
            )
            self.assertEqual(
                _source_ctx.instance.runtime_properties, {
                    '_set_changed': True,
                    'aws_resource_id': 'aws_resource_mock_id',
                    'resource_config': {
                        'DBSubnetGroupName': 'aws_target_mock_id'
                    },
                    'resource_id': 'prepare_attach_source'
                }
            )

    def test_prepare_assoc_OptionGroup(self):
        _source_ctx, _target_ctx, _ctx = self._create_instance_relationships(
            'test_prepare_assoc',
            ['cloudify.nodes.Root', 'cloudify.nodes.aws.rds.OptionGroup']
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')

        with patch('boto3.client', fake_boto):
            instance_read_replica.prepare_assoc(
                ctx=_ctx, resource_config=None, iface=None
            )
            self.assertEqual(
                _source_ctx.instance.runtime_properties, {
                    '_set_changed': True,
                    'aws_resource_id': 'aws_resource_mock_id',
                    'resource_config': {
                        'OptionGroupName': 'aws_target_mock_id'
                    },
                    'resource_id': 'prepare_attach_source'
                }
            )

    def test_prepare_assoc_Instance(self):
        _source_ctx, _target_ctx, _ctx = self._create_instance_relationships(
            'test_prepare_assoc',
            ['cloudify.nodes.Root', 'cloudify.nodes.aws.rds.Instance']
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')

        with patch('boto3.client', fake_boto):
            instance_read_replica.prepare_assoc(
                ctx=_ctx, resource_config=None, iface=None
            )
            self.assertEqual(
                _source_ctx.instance.runtime_properties, {
                    '_set_changed': True,
                    'aws_resource_id': 'aws_resource_mock_id',
                    'resource_config': {
                        'SourceDBInstanceIdentifier': 'aws_target_mock_id'
                    },
                    'resource_id': 'prepare_attach_source'
                }
            )

    def test_prepare_assoc_Role_NonRecoverableError(self):
        _source_ctx, _target_ctx, _ctx = self._create_instance_relationships(
            'test_prepare_assoc',
            ['cloudify.nodes.Root', 'cloudify.nodes.aws.iam.Role']
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')

        with patch('boto3.client', fake_boto):
            with self.assertRaises(NonRecoverableError) as error:
                instance_read_replica.prepare_assoc(
                    ctx=_ctx, resource_config=None, iface=None
                )
            self.assertEqual(
                str(error.exception),
                (
                    'Missing required relationship inputs ' +
                    '"iam_role_type_key" and/or "iam_role_id_key".'
                )
            )

    def test_prepare_assoc_Role(self):
        _source_ctx, _target_ctx, _ctx = self._create_instance_relationships(
            'test_prepare_assoc',
            ['cloudify.nodes.Root', 'cloudify.nodes.aws.iam.Role']
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')

        with patch('boto3.client', fake_boto):
            _target_ctx.instance.runtime_properties[
                'iam_role_id_key'] = 'role_field'
            instance_read_replica.prepare_assoc(
                ctx=_ctx, resource_config=None, iface=None,
                iam_role_type_key='iam_role_type_key',
                iam_role_id_key='iam_role_id_key'
            )
            self.assertEqual(
                _source_ctx.instance.runtime_properties, {
                    '_set_changed': True,
                    'aws_resource_id': 'aws_resource_mock_id',
                    'resource_config': {
                        'iam_role_type_key': 'role_field'
                    },
                    'resource_id': 'prepare_attach_source'
                }
            )

    def test_detach_from_Instance(self):
        _source_ctx, _target_ctx, _ctx = self._create_instance_relationships(
            'test_detach_from',
            ['cloudify.nodes.Root', 'cloudify.nodes.aws.rds.Instance']
        )
        current_ctx.set(_ctx)
        fake_boto, fake_client = self.fake_boto_client('rds')

        with patch('boto3.client', fake_boto):
            instance_read_replica.detach_from(
                ctx=_ctx, resource_config=None, iface=None
            )
            self.assertEqual(
                _source_ctx.instance.runtime_properties, {
                    '_set_changed': True,
                    'aws_resource_id': 'aws_resource_mock_id',
                    'resource_config': {},
                    'resource_id': 'prepare_attach_source'
                }
            )


if __name__ == '__main__':
    unittest.main()
