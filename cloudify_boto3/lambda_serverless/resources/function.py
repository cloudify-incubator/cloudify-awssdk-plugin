'''
    Serverless.Function
    ~~~~~~~~~~~~~~~~~~~
    AWS Lambda Function interface
'''
from os import remove as os_remove
from os.path import exists as path_exists
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.lambda_serverless import LambdaBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'Lambda Function'


class LambdaFunction(LambdaBase):
    '''
        AWS Lambda Function interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        LambdaBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        resource = None
        try:
            resource = self.client.get_function(FunctionName=self.resource_id)
        except ClientError:
            pass
        if not resource or not resource.get('Configuration', dict()):
            return None
        return resource['Configuration']

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def create(self, params):
        '''
            Create a new AWS Lambda Function.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_function(**params)
        self.logger.debug('Response: %s' % res)
        self.resource_id = res['FunctionName']
        return self.resource_id

    def delete(self, params=None):
        '''
            Deletes an existing AWS Lambda Function.
        '''
        params = params or dict()
        params.update(dict(FunctionName=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_function(**params)


@decorators.aws_resource(LambdaFunction, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS Lambda Function'''
    # Build API params
    params = resource_config
    params.update(dict(FunctionName=iface.resource_id))
    vpc_config = params.get('VpcConfig', dict())
    # Attach a Subnet Group if it exists
    subnet_ids = vpc_config.get('SubnetIds', list())
    for rel in utils.find_rels_by_node_type(
            ctx.instance, 'cloudify.aws.nodes.Subnet'):
        subnet_ids.append(utils.get_resource_id(
            node=rel.target.node,
            instance=rel.target.instance,
            raise_on_missing=True))
    vpc_config['SubnetIds'] = subnet_ids
    # Attach any security groups if they exist
    security_groups = vpc_config.get('SecurityGroupIds', list())
    for rel in utils.find_rels_by_node_type(
            ctx.instance, 'cloudify.aws.nodes.SecurityGroup'):
        security_groups.append(
            utils.get_resource_id(
                node=rel.target.node,
                instance=rel.target.instance,
                raise_on_missing=True))
    vpc_config['SecurityGroupIds'] = security_groups
    params['VpcConfig'] = vpc_config
    # Handle user-profided code ZIP file
    if params.get('Code', dict()).get('ZipFile'):
        codezip = params['Code']['ZipFile']
        ctx.logger.debug('ZipFile: "%s" (%s)' % (codezip, type(codezip)))
        if not path_exists(codezip):
            codezip = ctx.download_resource(codezip)
            ctx.logger.debug('Downloaded resource: "%s"' % codezip)
            with open(codezip, mode='rb') as _file:
                params['Code']['ZipFile'] = _file.read()
            ctx.logger.debug('Deleting resource: "%s"' % codezip)
            os_remove(codezip)
        else:
            with open(codezip, mode='rb') as _file:
                params['Code']['ZipFile'] = _file.read()
    # Actually create the resource
    utils.update_resource_id(ctx.instance, iface.create(params))


@decorators.aws_resource(LambdaFunction, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete()
def delete(ctx, iface, resource_config, **_):
    '''Deletes an AWS Lambda Function'''
    iface.delete(resource_config)
