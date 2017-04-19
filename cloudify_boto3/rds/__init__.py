# #######
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
'''
    RDS
    ~~~
    AWS RDS base interface
'''
# Cloudify AWS RDS
from cloudify_boto3.common import AWSResourceBase
from cloudify_boto3.rds.connection import RDSConnection

# pylint: disable=R0903


class RDSBase(AWSResourceBase):
    '''
        AWS RDS base interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        self.client = client or RDSConnection(ctx_node).client()
        AWSResourceBase.__init__(self, ctx_node, resource_id, client, logger)
