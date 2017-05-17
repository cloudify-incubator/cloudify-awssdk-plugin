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
from cloudify_boto3.common.tests.test_base import TestBase
from cloudify_boto3.autoscaling.resources import lifecycle_hook


# Constants
LIFECYCLE_HOOK_TH = ['cloudify.nodes.Root',
                     'cloudify.nodes.aws.autoscaling.LifecycleHook']


class TestAutoscalingLifecycleHook(TestBase):

    def test_prepare(self):
        self._prepare_check(
            type_hierarchy=LIFECYCLE_HOOK_TH,
            type_name='autoscaling',
            type_class=lifecycle_hook
        )


if __name__ == '__main__':
    unittest.main()
