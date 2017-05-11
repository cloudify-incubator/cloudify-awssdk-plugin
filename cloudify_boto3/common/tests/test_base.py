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

from mock import MagicMock
import unittest
import copy
from functools import wraps

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify.manager import DirtyTrackingDict
from botocore.exceptions import UnknownServiceError
from botocore.exceptions import ClientError

from cloudify_boto3.common import AWSResourceBase

CLIENT_CONFIG = {
    'aws_access_key_id': 'xxx',
    'aws_secret_access_key': 'yyy',
    'region_name': 'zzz'
}

DELETE_RESPONSE = {
    'ResponseMetadata': {
        'RetryAttempts': 0,
        'HTTPStatusCode': 200,
        'RequestId': 'xxxxxxxx',
        'HTTPHeaders': {
            'x-amzn-requestid': 'xxxxxxxx',
            'date': 'Fri, 28 Apr 2017 14:21:50 GMT',
            'content-length': '217',
            'content-type': 'text/xml'
        }
    }
}


def mock_decorator(*args, **kwargs):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class TestBase(unittest.TestCase):

    def tearDown(self):
        current_ctx.clear()
        super(TestBase, self).tearDown()

    def _to_DirtyTrackingDict(self, origin):
        if not origin:
            origin = {}
        dirty_dict = DirtyTrackingDict()
        for k in origin:
            dirty_dict[k] = copy.deepcopy(origin[k])
        return dirty_dict

    def get_mock_ctx(self,
                     test_name,
                     test_properties={},
                     test_runtime_properties={},
                     test_relationships=None,
                     type_hierarchy=['cloudify.nodes.Root']):

        ctx = MockCloudifyContext(
            node_id=test_name,
            deployment_id=test_name,
            properties=copy.deepcopy(test_properties),
            runtime_properties=self._to_DirtyTrackingDict(
                test_runtime_properties
            ),
            relationships=test_relationships,
            operation={'retry_number': 0}
        )

        ctx.node.type_hierarchy = type_hierarchy

        return ctx

    def get_mock_relationship_ctx(self,
                                  deployment_name,
                                  test_properties={},
                                  test_runtime_properties={},
                                  test_source=None,
                                  test_target=None,
                                  type_hierarchy=['cloudify.nodes.Root']):

        ctx = MockCloudifyContext(
            deployment_id=deployment_name,
            properties=copy.deepcopy(test_properties),
            source=test_source,
            target=test_target,
            runtime_properties=copy.deepcopy(test_runtime_properties))
        return ctx

    def _gen_client_error(self, name,
                          code='InvalidOptionGroupStateFault',
                          message='SomeThingIsGoingWrong'):
        return MagicMock(
            side_effect=ClientError(
                error_response={"Error": {
                    'Code': code,
                    'Message': message
                }},
                operation_name="client_error_" + name
            )
        )

    def _get_unknowservice(self, client_type):
        return MagicMock(
            side_effect=UnknownServiceError(
                service_name=client_type,
                known_service_names=['rds']
            )
        )

    def _fake_rds(self, fake_client, client_type):

        fake_client.create_db_instance_read_replica = self._get_unknowservice(
            client_type
        )
        fake_client.create_db_instance = self._get_unknowservice(client_type)
        fake_client.create_db_parameter_group = self._get_unknowservice(
            client_type
        )
        fake_client.create_db_subnet_group = self._get_unknowservice(
            client_type
        )
        fake_client.create_option_group = self._get_unknowservice(client_type)

        fake_client.describe_db_parameter_groups = self._gen_client_error(
            "db_parameter_groups"
        )
        fake_client.describe_db_subnet_groups = self._gen_client_error(
            "db_subnet_groups"
        )
        fake_client.describe_option_groups = self._gen_client_error(
            "option_groups"
        )
        fake_client.describe_db_instances = self._gen_client_error(
            "db_instances"
        )

        fake_client.modify_db_parameter_group = self._get_unknowservice(
            client_type
        )
        fake_client.modify_option_group = self._get_unknowservice(
            client_type
        )

        fake_client.delete_db_instance = self._get_unknowservice(
            client_type
        )
        fake_client.delete_db_parameter_group = self._get_unknowservice(
            client_type
        )
        fake_client.delete_db_subnet_group = self._get_unknowservice(
            client_type
        )
        fake_client.delete_option_group = self._get_unknowservice(client_type)

    def make_client_function(self, fun_name,
                             return_value=None,
                             side_effect=None,
                             client=None):
        if client:
            fake_client = client
        else:
            fake_client = MagicMock()
        fun = getattr(fake_client, fun_name)
        if side_effect is not None:
            fun.side_effect = side_effect
        elif return_value is not None:
            fun.return_value = return_value
        return fake_client

    def get_client_error_exception(self, name="Error"):
        return ClientError(error_response={"Error": {}},
                           operation_name=name)

    def get_unknown_service_exception(self, name="Error"):
        return UnknownServiceError(
            service_name=name,
            known_service_names=[name])

    def fake_boto_client(self, client_type):
        fake_client = MagicMock()
        if client_type == "rds":
            self._fake_rds(fake_client, client_type)
        return MagicMock(return_value=fake_client), fake_client

    def mock_return(self, value):
        return MagicMock(return_value=value)


class TestServiceBase(TestBase):

    base = None

    def test_properties(self):
        if not self.base:
            return
        with self.assertRaises(NotImplementedError):
            self.base.properties()

    def test_status(self):
        if not self.base:
            return
        with self.assertRaises(NotImplementedError):
            self.base.status()

    def test_create(self):
        if not self.base:
            return
        with self.assertRaises(NotImplementedError):
            self.base.create(None)

    def test_delete(self):
        if not self.base:
            return
        with self.assertRaises(NotImplementedError):
            self.base.delete(None)

    def test_update_resource_id(self):
        if not self.base:
            return
        self.base.update_resource_id('abc')
        self.assertEqual(self.base.resource_id, 'abc')


class TestAWSResourceBase(TestServiceBase):

    def setUp(self):
        self.base = AWSResourceBase("ctx_node", resource_id=True,
                                    logger=None)
