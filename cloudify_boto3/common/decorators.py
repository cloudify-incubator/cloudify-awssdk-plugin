'''
    Common.Decorators
    ~~~~~~~~~~~~~~~~~
    AWS decorators
'''
# Cloudify
from cloudify.exceptions import (OperationRetry, NonRecoverableError)
from cloudify_boto3.common import utils
from cloudify_boto3.common.constants import EXTERNAL_RESOURCE_ID as EXT_RES_ID


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
            # Override the resource ID if needed
            resource_id = kwargs.get(EXT_RES_ID)
            if resource_id and not \
                    ctx.instance.runtime_properties.get(EXT_RES_ID):
                ctx.instance.runtime_properties[EXT_RES_ID] = resource_id
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
            if not ignore_properties:
                # Normalize resource_config property
                resource_config = props.get('resource_config') or dict()
                resource_config_kwargs = resource_config.get('kwargs') or dict()
                if 'kwargs' in resource_config:
                    del resource_config['kwargs']
                resource_config.update(resource_config_kwargs)
                # Update the argument
                kwargs['resource_config'] = kwargs.get('resource_config') or \
                    resource_config or dict()
            # Check if using external
            if ctx.node.properties['use_external_resource']:
                resource_id = utils.get_resource_id(
                    node=ctx.node, instance=ctx.instance)
                ctx.logger.info('%s ID# "%s" is user-provided.'
                                % (resource_type, resource_id))
                if not kwargs.get('force_operation', False):
                    return
                ctx.logger.warn('%s ID# "%s" has force_operation set.'
                                % (resource_type, resource_id))
            return function(**kwargs)
        return wrapper_inner
    return wrapper_outer


def wait_for_status(status_good=None,
                    status_pending=None,
                    fail_on_missing=True):
    def wrapper_outer(function):
        def wrapper_inner(**kwargs):
            ctx = kwargs['ctx']
            resource_type = kwargs.get('resource_type', 'AWS Resource')
            iface = kwargs['iface']
            # Run the operation if this is the first pass
            if ctx.operation.retry_number == 0:
                function(**kwargs)
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
            elif status_good and status not in status_good:
                raise NonRecoverableError(
                    '%s ID# "%s" reported an unexpected status: "%s"'
                    % (resource_type, iface.resource_id, status))
        return wrapper_inner
    return wrapper_outer


def wait_for_delete(status_deleted=None, status_pending=None):
    def wrapper_outer(function):
        def wrapper_inner(**kwargs):
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
