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
    Common.Decorators
    ~~~~~~~~~~~~~~~~~
    AWS decorators
'''
# Cloudify imports
from cloudify.exceptions import (OperationRetry, NonRecoverableError)

# Local imports
from cloudify_awssdk.common import utils
from cloudify_awssdk.common.constants import (
    EXTERNAL_RESOURCE_ARN as EXT_RES_ARN,
    EXTERNAL_RESOURCE_ID as EXT_RES_ID)


def aws_relationship(class_decl=None,
                     resource_type='AWS Resource'):
    '''AWS resource decorator'''
    def wrapper_outer(function):
        '''Outer function'''
        def wrapper_inner(**kwargs):
            '''Inner, worker function'''
            ctx = kwargs['ctx']
            # Add new operation arguments
            kwargs['resource_type'] = resource_type
            kwargs['iface'] = class_decl(
                ctx.source.node, logger=ctx.logger,
                resource_id=utils.get_resource_id(
                    node=ctx.source.node,
                    instance=ctx.source.instance,
                    raise_on_missing=True)) if class_decl else None
            kwargs['resource_config'] = kwargs.get('resource_config') or dict()
            # Check if using external
            if ctx.source.node.properties.get('use_external_resource', False):
                resource_id = utils.get_resource_id(
                    node=ctx.source.node, instance=ctx.source.instance)
                ctx.logger.info('%s ID# "%s" is user-provided.'
                                % (resource_type, resource_id))
                if not kwargs.get('force_operation', False):
                    return
                ctx.logger.warn('%s ID# "%s" has force_operation set.'
                                % (resource_type, resource_id))
            # Execute the function
            ret = function(**kwargs)
            # When modifying nested runtime properties, the internal
            # "dirty checking" mechanism will not know of our changes.
            # This forces the internal tracking to mark the properties as
            # dirty and will be refreshed on next query.
            # pylint: disable=W0212
            ctx.source.instance.runtime_properties._set_changed()
            ctx.target.instance.runtime_properties._set_changed()
            return ret
        return wrapper_inner
    return wrapper_outer


def aws_resource(class_decl=None,
                 resource_type='AWS Resource',
                 ignore_properties=False):
    '''AWS resource decorator'''
    def wrapper_outer(function):
        '''Outer function'''
        def wrapper_inner(**kwargs):
            '''Inner, worker function'''
            ctx = kwargs['ctx']
            props = ctx.node.properties
            runtime_instance_properties = ctx.instance.runtime_properties
            # Override the resource ID if needed
            resource_id = kwargs.get(EXT_RES_ID)
            if resource_id and not \
                    ctx.instance.runtime_properties.get(EXT_RES_ID):
                ctx.instance.runtime_properties[EXT_RES_ID] = resource_id
            if resource_id and not \
                    ctx.instance.runtime_properties.get(EXT_RES_ARN):
                ctx.instance.runtime_properties[EXT_RES_ARN] = resource_id
            # Override any runtime properties if needed
            runtime_properties = kwargs.get('runtime_properties') or dict()
            for key, val in runtime_properties.iteritems():
                ctx.instance.runtime_properties[key] = val
            # Add new operation arguments
            kwargs['resource_type'] = resource_type
            kwargs['iface'] = class_decl(
                ctx.node, logger=ctx.logger,
                resource_id=utils.get_resource_id(
                    node=ctx.node,
                    instance=ctx.instance)) if class_decl else None

            resource_config = None
            if not ignore_properties:
                # Normalize resource_config property
                resource_config = props.get('resource_config') or dict()
                resource_config_kwargs = \
                    resource_config.get('kwargs') or dict()
                if 'kwargs' in resource_config:
                    del resource_config['kwargs']
                resource_config.update(resource_config_kwargs)
                # Update the argument
                kwargs['resource_config'] = kwargs.get('resource_config') or \
                    resource_config or dict()

                # ``resource_config`` could be part of the runtime instance
                # properties, If ``resource_config`` is empty then check if it
                # exists on runtime instance properties
                if not resource_config and runtime_instance_properties \
                        and runtime_instance_properties.get('resource_config'):
                    kwargs['resource_config'] =\
                        runtime_instance_properties['resource_config']
                    resource_config = kwargs['resource_config']

            # Check if using external
            if ctx.node.properties.get('use_external_resource', False):
                resource_id = utils.get_resource_id(
                    node=ctx.node, instance=ctx.instance)
                ctx.logger.info('%s ID# "%s" is user-provided.'
                                % (resource_type, resource_id))
                if not kwargs.get('force_operation', False):
                    # If ``force_operation`` is not set then we need to make
                    #  sure that runtime properties for node instance are
                    # setting correctly
                    # Set ``resource_config`` and ``EXT_RES_ID``
                    ctx.instance.runtime_properties[
                        'resource_config'] = resource_config
                    ctx.instance.runtime_properties[EXT_RES_ID] = resource_id
                    return
                ctx.logger.warn('%s ID# "%s" has force_operation set.'
                                % (resource_type, resource_id))
            return function(**kwargs)
        return wrapper_inner
    return wrapper_outer


def wait_for_status(status_good=None,
                    status_pending=None,
                    fail_on_missing=True):
    '''AWS resource decorator'''
    def wrapper_outer(function):
        '''Outer function'''
        def wrapper_inner(**kwargs):
            '''Inner, worker function'''
            ctx = kwargs['ctx']
            resource_type = kwargs.get('resource_type', 'AWS Resource')
            iface = kwargs['iface']
            # Run the operation if this is the first pass
            if ctx.operation.retry_number == 0:
                function(**kwargs)
                # Fixes https://github.com/cloudify-incubator/cloudify-awssdk-plugin/issues/128
                # and https://github.com/cloudify-incubator/cloudify-awssdk-plugin/issues/129
                # by updating iface object with actual details from the AWS response
                # assuming that actual state is available at ctx.instance.runtime_properties['create_response']
                # and ctx.instance.runtime_properties['aws_resource_id'] correctly updated after creation

                # At first let's verify was a new AWS resource really created
                if iface.resource_id != ctx.instance.runtime_properties['aws_resource_id']:
                    # Assuming new resource was really created, so updating iface object
                    iface.resource_id = ctx.instance.runtime_properties['aws_resource_id']
                    # If sequence of install -> uninstall workflows was executed, we should remove '__deleted'
                    # flag set in the decorator wait_for_delete below
                    if '__deleted' in ctx.instance.runtime_properties:
                        del ctx.instance.runtime_properties['__deleted']

            # Get a resource interface and query for the status
            status = iface.status
            ctx.logger.debug('%s ID# "%s" reported status: %s'
                             % (resource_type, iface.resource_id, status))
            if status_pending and status in status_pending:
                raise OperationRetry(
                    '%s ID# "%s" is still in a pending state.'
                    % (resource_type, iface.resource_id))
            elif not status and fail_on_missing:
                raise NonRecoverableError(
                    '%s ID# "%s" no longer exists but "fail_on_missing" set'
                    % (resource_type, iface.resource_id))
            elif status_good and status not in status_good and fail_on_missing:
                raise NonRecoverableError(
                    '%s ID# "%s" reported an unexpected status: "%s"'
                    % (resource_type, iface.resource_id, status))
        return wrapper_inner
    return wrapper_outer


def wait_for_delete(status_deleted=None, status_pending=None):
    '''AWS resource decorator'''
    def wrapper_outer(function):
        '''Outer function'''
        def wrapper_inner(**kwargs):
            '''Inner, worker function'''
            ctx = kwargs['ctx']
            resource_type = kwargs.get('resource_type', 'AWS Resource')
            iface = kwargs['iface']
            # Run the operation if this is the first pass
            if not ctx.instance.runtime_properties.get('__deleted', False):
                function(**kwargs)
                ctx.instance.runtime_properties['__deleted'] = True
            # Get a resource interface and query for the status
            status = iface.status
            ctx.logger.debug('%s ID# "%s" reported status: %s'
                             % (resource_type, iface.resource_id, status))
            if not status or (status_deleted and status in status_deleted):
                return
            elif status_pending and status in status_pending:
                raise OperationRetry(
                    '%s ID# "%s" is still in a pending state.'
                    % (resource_type, iface.resource_id))
            raise NonRecoverableError(
                '%s ID# "%s" reported an unexpected status: "%s"'
                % (resource_type, iface.resource_id, status))
        return wrapper_inner
    return wrapper_outer
