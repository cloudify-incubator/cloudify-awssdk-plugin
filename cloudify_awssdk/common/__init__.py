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
    Common
    ~~~~~~
    AWS common interfaces
'''
from logging import NullHandler
# Cloudify
from cloudify.logs import init_cloudify_logger


class AWSResourceBase(object):
    '''
        AWS base interface
    '''
    def __init__(self, client, resource_id=None, logger=None):
        self.logger = logger or init_cloudify_logger(NullHandler(),
                                                     'AWSResourceBase')
        self.client = client
        self.resource_id = str(resource_id) if resource_id else None

    def update_resource_id(self, resource_id):
        '''Updates the resource_id value'''
        self.resource_id = resource_id

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        raise NotImplementedError()

    @property
    def status(self):
        '''Gets the status of an external resource'''
        raise NotImplementedError()

    def create(self, params):
        '''Creates a resource'''
        raise NotImplementedError()

    def delete(self, params=None):
        '''Deletes a resource'''
        raise NotImplementedError()
