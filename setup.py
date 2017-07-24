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
"""Cloudify plugin package config"""

from setuptools import setup


setup(
    name='cloudify-awssdk-plugin',
    version='1.0.0',
    license='LICENSE',
    packages=[
        'cloudify_awssdk',
        'cloudify_awssdk.common',
        'cloudify_awssdk.autoscaling',
        'cloudify_awssdk.autoscaling.resources',
        'cloudify_awssdk.cloudwatch',
        'cloudify_awssdk.cloudwatch.resources',
        'cloudify_awssdk.cloudformation',
        'cloudify_awssdk.cloudformation.resources',
        'cloudify_awssdk.dynamodb',
        'cloudify_awssdk.dynamodb.resources',
        'cloudify_awssdk.ec2',
        'cloudify_awssdk.ec2.resources',
        'cloudify_awssdk.efs',
        'cloudify_awssdk.efs.resources',
        'cloudify_awssdk.elb',
        'cloudify_awssdk.elb.resources',
        'cloudify_awssdk.elb.resources.classic',
        'cloudify_awssdk.iam',
        'cloudify_awssdk.iam.resources',
        'cloudify_awssdk.kms',
        'cloudify_awssdk.kms.resources',
        'cloudify_awssdk.lambda_serverless',
        'cloudify_awssdk.lambda_serverless.resources',
        'cloudify_awssdk.rds',
        'cloudify_awssdk.rds.resources',
        'cloudify_awssdk.route53',
        'cloudify_awssdk.route53.resources',
        'cloudify_awssdk.s3',
        'cloudify_awssdk.s3.resources',
        'cloudify_awssdk.sns',
        'cloudify_awssdk.sns.resources',
        'cloudify_awssdk.sqs',
        'cloudify_awssdk.sqs.resources'
    ],
    description='A Cloudify plugin for AWS',
    install_requires=[
        'cloudify-plugins-common>=3.4',
        'boto3==1.4.4',
        'botocore==1.5.44'
    ]
)
