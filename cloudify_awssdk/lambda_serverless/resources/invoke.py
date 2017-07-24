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
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.lambda_serverless.resources.function import LambdaFunction

RESOURCE_TYPE = 'Lambda Function Invocation'


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def configure(ctx, resource_config, **_):
    '''Configures an AWS Lambda Invoke'''
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_relationship(resource_type=RESOURCE_TYPE)
def attach_to(ctx, resource_config, **_):
    '''Attaches an Lambda Invoke to something else'''
    rtprops = ctx.source.instance.runtime_properties
    if utils.is_node_type(ctx.target.node,
                          'cloudify.nodes.aws.lambda.Function'):
        ctx.source.instance.runtime_properties['output'] = LambdaFunction(
            ctx.target.node, logger=ctx.logger,
            resource_id=utils.get_resource_id(
                node=ctx.target.node,
                instance=ctx.target.instance,
                raise_on_missing=True)).invoke(
                    resource_config or rtprops.get('resource_config'))


@decorators.aws_relationship(resource_type=RESOURCE_TYPE)
def detach_from(ctx, resource_config, **_):
    '''Detaches an Lambda Invoke from something else'''
    pass
