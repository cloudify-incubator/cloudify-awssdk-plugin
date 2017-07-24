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
    Lambda.Permission
    ~~~~~~~~~~~~~~~~~
    AWS Lambda Permission interface
'''
from uuid import uuid4
# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.lambda_serverless import LambdaBase

RESOURCE_TYPE = 'Lambda Permission'


class LambdaPermission(LambdaBase):
    '''
        AWS Lambda Permission interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        LambdaBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        raise NotImplementedError()

    @property
    def status(self):
        '''Gets the status of an external resource'''
        raise NotImplementedError()

    def create(self, params):
        '''
            Create a new AWS Lambda Permission.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.add_permission(**params)
        self.logger.debug('Response: %s' % res)
        self.update_resource_id(params.get('StatementId'))
        return self.resource_id, self.resource_id

    def delete(self, params=None):
        '''
            Deletes an existing AWS Lambda Permission.
        '''
        params = params or dict()
        params.update(dict(StatementId=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.remove_permission(**params)


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    '''Prepares an AWS Lambda Permission'''
    # Save the parameters
    if not utils.get_resource_id():
        if resource_config.get('StatementId'):
            utils.update_resource_id(
                ctx.instance, resource_config['StatementId'])
        else:
            utils.update_resource_id(ctx.instance, str(uuid4()))
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(LambdaPermission, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS Lambda Permission'''
    # Build API params
    params = ctx.instance.runtime_properties['resource_config'] or dict()
    if not iface.resource_id and params.get('StatementId'):
        utils.update_resource_id(ctx.instance, params['StatementId'])
    params.update(dict(StatementId=iface.resource_id))
    # Actually create the resource
    res_id, res_arn = iface.create(params)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_arn)


@decorators.aws_resource(LambdaPermission, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS Lambda Permission'''
    # Build API params
    resource_config.update(dict(
        FunctionName=ctx.instance.runtime_properties[
            'resource_config'].get('FunctionName')))
    iface.delete(resource_config)


@decorators.aws_relationship(LambdaPermission, RESOURCE_TYPE)
def prepare_assoc(ctx, iface, resource_config, **_):
    '''Prepares to associate an Lambda Permission to something else'''
    if utils.is_node_type(ctx.target.node,
                          'cloudify.nodes.aws.lambda.Function'):
        ctx.source.instance.runtime_properties[
            'resource_config']['FunctionName'] = utils.get_resource_arn(
                node=ctx.target.node,
                instance=ctx.target.instance,
                raise_on_missing=True)


@decorators.aws_relationship(LambdaPermission, RESOURCE_TYPE)
def detach_from(ctx, iface, resource_config, **_):
    '''Detaches an Lambda Permission from something else'''
    pass
