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
    Serverless.Invoke
    ~~~~~~~~~~~~~~~~~
    AWS Lambda Function invocation interface
'''
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.common.connection import Boto3Connection

RESOURCE_TYPE = 'Lambda Function Invocation'


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def start(ctx, resource_config, **_):
    '''Starts an AWS Lambda Function invocation'''
    # Build API params
    params = resource_config
    params.update(dict(FunctionName=utils.get_resource_id()))
    # Attach a Lambda Function if it exists
    lambda_function = utils.find_rel_by_node_type(
        ctx.instance, 'cloudify.nodes.aws.lambda.Function')
    if lambda_function:
        params['FunctionName'] = utils.get_resource_id(
            node=lambda_function.target.node,
            instance=lambda_function.target.instance,
            raise_on_missing=True)
    # Invoke the function
    client = Boto3Connection(ctx.node).client('lambda')
    ctx.logger.debug('Starting %s with parameters: %s'
                     % (RESOURCE_TYPE, params))
    res = client.invoke(**params)
    if res and res.get('Payload'):
        res['Payload'] = res['Payload'].read()
    ctx.logger.debug('Response: %s' % res)
    # Update runtime properties
    utils.update_resource_id(ctx.instance, params['FunctionName'])
    try:
        ctx.instance.runtime_properties['output'] = res
    except TypeError:
        pass
