'''
    Common
    ~~~~~~
    AWS common interfaces
'''
from logging import NullHandler
# Cloudify
from cloudify.logs import init_cloudify_logger


class AWSResourceBase(object):
    '''
        AWS base interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        self.logger = logger or init_cloudify_logger(NullHandler(),
                                                     'AWSResourceBase')
        self.resource_id = str(resource_id) if resource_id else None

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        raise NotImplementedError()

    @property
    def status(self):
        '''Gets the status of an external resource'''
        raise NotImplementedError()

    def create(self, params):
        '''Creates a resource'''
        raise NotImplementedError()

    def delete(self, params=None):
        '''Deletes a resource'''
        raise NotImplementedError()
