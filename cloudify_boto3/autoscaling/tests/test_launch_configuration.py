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
from cloudify_boto3.common.tests.test_base import TestBase, CLIENT_CONFIG
from cloudify_boto3.autoscaling.resources import launch_configuration


# Constants
LAUNCH_CONFIGURATION_TH = [
    'cloudify.nodes.Root',
    'cloudify.nodes.aws.autoscaling.LaunchConfiguration'
]

NODE_PROPERTIES = {
    'use_external_resource': False,
    'resource_config': {},
    'client_config': CLIENT_CONFIG
}

RUNTIME_PROPERTIES = {
    'aws_resource_id': 'aws_resource',
    'resource_config': {}
}


class TestAutoscalingLaunchConfiguration(TestBase):

    def test_prepare(self):
        self._prepare_check(
            type_hierarchy=LAUNCH_CONFIGURATION_TH,
            type_name='autoscaling',
            type_class=launch_configuration
        )


if __name__ == '__main__':
    unittest.main()
