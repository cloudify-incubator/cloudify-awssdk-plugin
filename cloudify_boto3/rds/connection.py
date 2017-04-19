'''
    RDS.Connection
    ~~~~~~~~~~~~~~
    AWS RDS connection
'''
# Boto
import boto3
# Cloudify
from cloudify_boto3.common.constants import AWS_CONFIG_PROPERTY

# pylint: disable=R0903


class RDSConnection(object):
    '''
        Provides a sugared connection to the AWS RDS service

    :param `cloudify.context.NodeContext` node: A Cloudify node
    :param dict aws_config: AWS connection configuration overrides
    '''
    def __init__(self, node, aws_config=None):
        aws_config_whitelist = [
            'aws_access_key_id', 'aws_secret_access_key', 'region_name']
        self.aws_config = node.properties.get(AWS_CONFIG_PROPERTY, dict())
        # Merge user-provided AWS config with generated config
        self.aws_config.update(aws_config or dict())
        # Prepare region name for Boto
        self.aws_config['region_name'] = self.aws_config.get('region_name')
        # Delete all non-whitelisted keys
        self.aws_config = {k: v for k, v in self.aws_config.iteritems()
                           if k in aws_config_whitelist}

    def client(self):
        '''
            Builds an AWS RDS connection client

        :returns: An AWS RDS boto3 client
        :rtype: `boto.rds.connection.RdsConnection`
        :raises: :exc:`cloudify.exceptions.NonRecoverableError`
        '''
        return boto3.client('rds', **self.aws_config)
