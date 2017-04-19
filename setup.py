'''Cloudify plugin package config'''

from setuptools import setup


setup(
    name='cloudify-boto3-plugin',
    version='1.0',
    license='LICENSE',
    packages=[
        'cloudify_boto3',
        'cloudify_boto3.common',
        'cloudify_boto3.rds',
        'cloudify_boto3.rds.resources',
        'cloudify_boto3.lambda_serverless',
        'cloudify_boto3.lambda_serverless.resources'
    ],
    description='A Cloudify plugin for AWS',
    install_requires=[
        'cloudify-plugins-common>=3.4',
        'boto3==1.4.4',
        'botocore==1.5.39'
    ]
)
