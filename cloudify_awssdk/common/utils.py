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
    Common.Utils
    ~~~~~~~~~~~~
    AWS helper utilities
'''
# Generic
import re
import uuid
# Cloudify
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify_awssdk.common import constants


def get_resource_string(
        node=None, instance=None,
        property_key=None, attribute_key=None):
    '''
        Gets a string of a Cloudify node and/or instance, searching
        both properties and runtime properties (attributes).
    :param `cloudify.context.NodeContext` node:
        Cloudify node.
    :param `cloudify.context.NodeInstanceContext` instance:
        Cloudify node instance.
    '''
    node = node if node else ctx.node
    instance = instance if instance else ctx.instance
    props = node.properties if node else {}
    runtime_props = instance.runtime_properties if instance else {}
    # Search instance runtime properties first, then the node properties
    value = runtime_props.get(attribute_key, props.get(property_key))
    return str(value) if value else None


def get_resource_id(node=None,
                    instance=None,
                    resource_name=None,
                    use_instance_id=False,
                    raise_on_missing=False):
    '''
        Gets the (external) resource ID of a Cloudify node and/or instance.
        depending on the environment available.
    :param `cloudify.context.NodeContext` node:
        Cloudify node.
    :param `cloudify.context.NodeInstanceContext` instance:
        Cloudify node instance.
    :param boolean raise_on_missing: If True, causes this method to raise
        an exception if the resource ID is not found.
    :param string resource_name: [RESOURCE_]NAME as set in resource_config.
        For example "LaunchConfigurationName".
    :raises: :exc:`cloudify.exceptions.NonRecoverableError`
    '''
    resource_id = get_resource_string(
        node, instance, 'resource_id', constants.EXTERNAL_RESOURCE_ID)
    if not resource_id and raise_on_missing:
        raise NonRecoverableError(
            'Missing resource ID! Node=%s, Instance=%s' % (
                node.id if node else None,
                instance.id if instance else None))
    elif resource_name and not resource_id:
        return resource_name
    elif use_instance_id and not resource_id:
        return ctx.instance.id
    return resource_id


def get_resource_arn(node=None, instance=None,
                     raise_on_missing=False):
    '''
        Gets the (external) resource ARN of a Cloudify node and/or instance.
        depending on the environment available.
    :param `cloudify.context.NodeContext` node:
        Cloudify node.
    :param `cloudify.context.NodeInstanceContext` instance:
        Cloudify node instance.
    :param boolean raise_on_missing: If True, causes this method to raise
        an exception if the resource ID is not found.
    :raises: :exc:`cloudify.exceptions.NonRecoverableError`
    '''
    resource_id = get_resource_string(
        node, instance, 'resource_arn', constants.EXTERNAL_RESOURCE_ARN)
    if not resource_id and raise_on_missing:
        raise NonRecoverableError(
            'Missing resource ARN! Node=%s, Instance=%s' % (
                node.id if node else None,
                instance.id if instance else None))
    return resource_id


def update_resource_id(instance, val):
    '''Updates an instance's resource ID'''
    instance.runtime_properties[constants.EXTERNAL_RESOURCE_ID] = str(val)


def update_resource_arn(instance, val):
    '''Updates an instance's resource ARN'''
    instance.runtime_properties[constants.EXTERNAL_RESOURCE_ARN] = str(val)


def get_parent_resource_id(node_instance,
                           rel_type=constants.REL_CONTAINED_IN,
                           raise_on_missing=True):
    '''Finds a relationship to a parent and gets its resource ID'''
    rel = find_rel_by_type(node_instance, rel_type)
    if not rel:
        if raise_on_missing:
            raise NonRecoverableError('Error locating parent resource ID')
        return None
    return get_resource_id(instance=rel.target.instance,
                           raise_on_missing=raise_on_missing)


def get_ancestor_resource_id(node_instance,
                             node_type,
                             raise_on_missing=True):
    '''Finds an ancestor and gets its resource ID'''
    ancestor = get_ancestor_by_type(node_instance, node_type)
    if not ancestor:
        if raise_on_missing:
            raise NonRecoverableError('Error locating ancestor resource ID')
        return None
    return get_resource_id(instance=ancestor.instance,
                           raise_on_missing=raise_on_missing)


def filter_boto_params(args, filters, preserve_none=False):
    '''
        Takes in a dictionary, applies a "whitelist" of key names,
        and removes keys which have associated values of None.

    :param dict args: Original dictionary to filter
    :param list filters: Whitelist list of keys
    :param boolean preserve_none: If True, keeps key-value pairs even
        if the value is None.
    '''
    return {
        k: v for k, v in args.iteritems()
        if k in filters and (preserve_none is True or v is not None)
    }


def find_rels_by_type(node_instance, rel_type):
    '''
        Finds all specified relationships of the Cloudify
        instance.
    :param `cloudify.context.NodeInstanceContext` node_instance:
        Cloudify node instance.
    :param str rel_type: Cloudify relationship type to search
        node_instance.relationships for.
    :returns: List of Cloudify relationships
    '''
    return [x for x in node_instance.relationships
            if rel_type in x.type_hierarchy]


def find_rel_by_type(node_instance, rel_type):
    '''
        Finds a single relationship of the Cloudify instance.
    :param `cloudify.context.NodeInstanceContext` node_instance:
        Cloudify node instance.
    :param str rel_type: Cloudify relationship type to search
        node_instance.relationships for.
    :returns: A Cloudify relationship or None
    '''
    rels = find_rels_by_type(node_instance, rel_type)
    return rels[0] if len(rels) > 0 else None


def find_rels_by_node_type(node_instance, node_type):
    '''
        Finds all specified relationships of the Cloudify
        instance where the related node type is of a specified type.
    :param `cloudify.context.NodeInstanceContext` node_instance:
        Cloudify node instance.
    :param str node_type: Cloudify node type to search
        node_instance.relationships for.
    :returns: List of Cloudify relationships
    '''
    return [x for x in node_instance.relationships
            if node_type in x.target.node.type_hierarchy]


def find_rel_by_node_type(node_instance, node_type):
    '''
        Finds a single relationship of the Cloudify
        instance where the related node type is of a specified type.
    :param `cloudify.context.NodeInstanceContext` node_instance:
        Cloudify node instance.
    :param str rel_type: Cloudify relationship type to search
        node_instance.relationships for.
    :returns: A Cloudify relationship or None
    '''
    rels = find_rels_by_node_type(node_instance, node_type)
    return rels[0] if len(rels) > 0 else None


def find_rels_by_node_name(node_instance, node_name):
    '''
        Finds all specified relationships of the Cloudify
        instance where the related node type is of a specified type.
    :param `cloudify.context.NodeInstanceContext` node_instance:
        Cloudify node instance.
    :param str node_bane: Cloudify node name to search
        node_instance.relationships for.
    :returns: List of Cloudify relationships
    '''
    return [x for x in node_instance.relationships
            if node_name in x.target.node.id]


def is_node_type(node, node_type):
    '''
        Checks if a node is of a given node type.
    :returns: `True` or `False`
    '''
    return node_type in node.type_hierarchy


def get_ancestor_by_type(inst, node_type):
    '''
        Gets an ancestor context (recursive search)
    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string node_type: Node type name
    :returns: Ancestor context or None
    '''
    # Find a parent of a specific type
    rel = find_rel_by_type(inst, 'cloudify.relationships.contained_in')
    if not rel:
        return None
    if node_type in rel.target.node.type_hierarchy:
        return rel.target
    return get_ancestor_by_type(rel.target.instance, node_type)


def add_resources_from_rels(node_instance, node_type, current_list):
    '''
        Updates a resource list with relationships same target types
    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string node_type: Node type name
    :param current_list: List of IDs
    :return: updated list
    '''
    resources = \
        find_rels_by_node_type(
            node_instance,
            node_type)
    for resource in resources:
        resource_id = \
            resource.target.instance.runtime_properties[
                constants.EXTERNAL_RESOURCE_ID]
        if resource_id not in current_list:
            current_list.append(resource_id)
    return current_list


def find_resource_id_by_type(node_instance, node_type):
    '''
        Finds the resource_id of a single node,
        which is connected via a relationship.
    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string node_type: Node type name
    :return: None or the resource id
    '''

    targ = \
        find_rel_by_node_type(
            node_instance,
            node_type)
    if targ and getattr(targ, 'target'):
        resource_id = \
            targ.target.instance.runtime_properties.get(
                constants.EXTERNAL_RESOURCE_ID)
        return resource_id
    return None


def find_resource_arn_by_type(node_instance, node_type):
    '''
        Finds the resource_arn of a single node,
        which is connected via a relationship.
    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string node_type: Node type name
    :return: None or the resource arn
    '''

    targ = \
        find_rel_by_node_type(
            node_instance,
            node_type)
    if targ and getattr(targ, 'target'):
        resource_id = \
            targ.target.instance.runtime_properties.get(
                constants.EXTERNAL_RESOURCE_ARN)
        return resource_id
    return None


def validate_arn(arn_candidate, arn_regex=constants.ARN_REGEX):
    arn_matcher = re.compile(arn_regex)
    return arn_matcher.match(arn_candidate)


def get_uuid():
    return str(uuid.uuid4())
