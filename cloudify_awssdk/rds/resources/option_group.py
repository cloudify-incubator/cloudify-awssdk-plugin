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
    RDS.OptionGroup
    ~~~~~~~~~~~~~~~
    AWS RDS Option Group interface
'''
# Cloudify
from cloudify.exceptions import OperationRetry
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.rds import RDSBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'RDS Option Group'


class OptionGroup(RDSBase):
    '''
        AWS RDS Option Group interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        RDSBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        resources = None
        try:
            resources = self.client.describe_option_groups(
                OptionGroupName=self.resource_id)
        except ClientError:
            pass
        if not resources or not resources.get('OptionGroupsList', list()):
            return None
        return resources['OptionGroupsList'][0]

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def include_option(self, option):
        '''Adds an option to an AWS RDS option group'''
        self.logger.debug('Including option in option group: %s' % option)
        return self.client.modify_option_group(**dict(
            OptionGroupName=self.resource_id,
            OptionsToInclude=[option],
            ApplyImmediately=True))['OptionGroup']

    def remove_option(self, option_id):
        '''Removes an option from an AWS RDS option group'''
        self.logger.debug('Removing option from option group: %s' % option_id)
        return self.client.modify_option_group(**dict(
            OptionGroupName=self.resource_id,
            OptionsToRemove=[option_id],
            ApplyImmediately=True))['OptionGroup']

    def create(self, params):
        '''
            Create a new AWS RDS option group.
        .. note:
            See http://bit.ly/2ownCxX for config details.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_option_group(**params)
        self.logger.debug('Response: %s' % res)
        self.update_resource_id(res['OptionGroup']['OptionGroupName'])
        return self.resource_id, res['OptionGroup']['OptionGroupArn']

    def delete(self, params=None):
        '''
            Deletes an existing AWS RDS option group.
        .. note:
            See http://bit.ly/2pC0sWj for config details.
        '''
        params = params or dict()
        params.update(dict(OptionGroupName=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_option_group(**params)


@decorators.aws_resource(OptionGroup, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS RDS Option Group'''
    # Build API params
    resource_config.update(dict(OptionGroupName=iface.resource_id))
    # Actually create the resource
    res_id, res_arn = iface.create(resource_config)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_arn)


@decorators.aws_resource(OptionGroup, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete(status_pending=['available'])
def delete(iface, resource_config, **_):
    '''Deletes an AWS RDS Option Group'''
    try:
        iface.delete(resource_config)
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'InvalidOptionGroupStateFault':
            raise OperationRetry(exc.response['Error']['Message'])
        raise exc


@decorators.aws_relationship(OptionGroup, RESOURCE_TYPE)
def attach_to(ctx, iface, resource_config, **_):
    '''Attaches an RDS OptionGroup to something else'''
    rtprops = ctx.target.instance.runtime_properties
    params = resource_config or rtprops.get('resource_config') or dict()
    if utils.is_node_type(ctx.target.node,
                          'cloudify.nodes.aws.rds.Option'):
        params['OptionName'] = utils.get_resource_id(
            node=ctx.target.node,
            instance=ctx.target.instance,
            raise_on_missing=True)
        iface.include_option(params)


@decorators.aws_relationship(OptionGroup, RESOURCE_TYPE)
def detach_from(ctx, iface, resource_config, **_):
    '''Detaches an RDS OptionGroup from something else'''
    if utils.is_node_type(ctx.target.node,
                          'cloudify.nodes.aws.rds.Option'):
        iface.remove_option(utils.get_resource_id(
            node=ctx.target.node,
            instance=ctx.target.instance,
            raise_on_missing=True))
