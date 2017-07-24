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
    IAM.Role
    ~~~~~~~~
    AWS IAM Role interface
'''
from json import dumps as json_dumps
# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.iam import IAMBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'IAM Role'
RESOURCE_NAME = 'RoleName'


class IAMRole(IAMBase):
    '''
        AWS IAM Role interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        IAMBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        resource = None
        try:
            resource = self.client.get_role(RoleName=self.resource_id)
        except ClientError:
            pass
        if not resource or not resource.get('Role', dict()):
            return None
        return resource['Role']

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def create(self, params):
        '''
            Create a new AWS IAM Role.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_role(**params)
        self.logger.debug('Response: %s' % res)
        self.update_resource_id(res['Role']['RoleName'])
        return self.resource_id, res['Role']['Arn']

    def delete(self, params=None):
        '''
            Deletes an existing AWS IAM Role.
        '''
        params = params or dict()
        params.update(dict(RoleName=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_role(**params)

    def attach_policy(self, params):
        '''
            Attaches an IAM Policy to an IAM Role
        '''
        self.logger.debug('Attaching IAM Policy "%s" to IAM Role "%s"'
                          % (params.get('PolicyArn'), self.resource_id))
        params = params or dict()
        params.update(dict(RoleName=self.resource_id))
        self.client.attach_role_policy(**params)

    def detach_policy(self, params):
        '''
            Detaches an IAM Policy from an IAM Role
        '''
        self.logger.debug('Detaching IAM Policy "%s" from IAM Role "%s"'
                          % (params.get('PolicyArn'), self.resource_id))
        params = params or dict()
        params.update(dict(RoleName=self.resource_id))
        self.client.detach_role_policy(**params)


@decorators.aws_resource(IAMRole, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS IAM Role'''
    # Build API params
    params = \
        dict() if not resource_config else resource_config.copy()
    resource_id = \
        utils.get_resource_id(
            ctx.node,
            ctx.instance,
            params.get(RESOURCE_NAME),
            use_instance_id=True
        ) or iface.resource_id
    params[RESOURCE_NAME] = resource_id
    utils.update_resource_id(ctx.instance, resource_id)

    if 'AssumeRolePolicyDocument' in params and \
            isinstance(params['AssumeRolePolicyDocument'], dict):
        params['AssumeRolePolicyDocument'] = \
            json_dumps(params['AssumeRolePolicyDocument'])
    # Actually create the resource
    res_id, res_arn = iface.create(params)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_arn)


@decorators.aws_resource(IAMRole, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete()
def delete(iface, resource_config, **_):
    '''Deletes an AWS IAM Role'''
    iface.delete(resource_config)


@decorators.aws_relationship(IAMRole, RESOURCE_TYPE)
def attach_to(ctx, iface, resource_config, **_):
    '''Attaches an IAM Role to something else'''
    if utils.is_node_type(ctx.target.node,
                          'cloudify.nodes.aws.iam.Policy'):
        resource_config['PolicyArn'] = utils.get_resource_arn(
            node=ctx.target.node,
            instance=ctx.target.instance,
            raise_on_missing=True)
        iface.attach_policy(resource_config)


@decorators.aws_relationship(IAMRole, RESOURCE_TYPE)
def detach_from(ctx, iface, resource_config, **_):
    '''Detaches an IAM Role from something else'''
    if utils.is_node_type(ctx.target.node,
                          'cloudify.nodes.aws.iam.Policy'):
        resource_config['PolicyArn'] = utils.get_resource_arn(
            node=ctx.target.node,
            instance=ctx.target.instance,
            raise_on_missing=True)
        iface.detach_policy(resource_config)
