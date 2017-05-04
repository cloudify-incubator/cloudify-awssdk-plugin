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
    S3.Bucket
    ~~~~~~~~~~~~~~
    AWS S3 Bucket interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.s3 import S3Base
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'S3 Bucket'
BUCKET = 'Bucket'


class S3Bucket(S3Base):
    '''
        AWS S3 Bucket interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        S3Base.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        try:
            resources = self.client.list_buckets()
        except ClientError:
            pass
        else:
            for resource in resources:
                if resource.get('Name') is self.resource_id:
                    return resource
            return None

    @property
    def status(self):
        '''Gets the status of an external resource'''
        props = self.properties
        if not props:
            return None
        return props['Status']

    def create(self, params):
        '''
            Create a new AWS S3 Bucket.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_bucket(**params)
        self.logger.debug('Response: %s' % res)
        return res['Location']

    def delete(self, params=None):
        '''
            Deletes an existing AWS S3 Bucket.
        '''
        if BUCKET not in params.keys():
            params.update({BUCKET: self.resource_id})
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_bucket(**params)


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS S3 Bucket'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(S3Bucket, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS S3 Bucket'''
    params = resource_config.copy()
    bucket_name = params.get(BUCKET)
    utils.update_resource_id(ctx.instance, bucket_name)
    # Actually create the resource
    bucket_location = iface.create(resource_config)
    ctx.instance.runtime_properties['Location'] = \
        bucket_location


@decorators.aws_resource(S3Bucket, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    '''Deletes an AWS S3 Bucket'''
    iface.delete(resource_config)
