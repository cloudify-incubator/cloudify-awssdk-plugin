# Built-in Imports
import os
import re
import tempfile

# Cloudify Imports
from ecosystem_tests import TestLocal, utils, IP_ADDRESS_REGEX, create_password


NODE_TYPE_PREFIX = 'cloudify.nodes.aws'


class TestAWSSDK(TestLocal):

    def setUp(self):

        if 'ECOSYSTEM_SESSION_PASSWORD' not in os.environ:
            os.environ['ECOSYSTEM_SESSION_PASSWORD'] = create_password()
        self.password = os.environ['ECOSYSTEM_SESSION_PASSWORD']
        sensitive_data = [
            os.environ['AWS_SECRET_ACCESS_KEY'],
            os.environ['AWS_ACCESS_KEY_ID'],
            self.password
        ]
        os.environ['AWS_DEFAULT_REGION'] = \
            self.inputs().get('ec2_region_name')
        os.environ['TEST_APPLICATION_PREFIX'] = \
            os.environ['CIRCLE_BUILD_NUM']
        super(TestAWSSDK, self).setUp(
            'aws.yaml', sensitive_data=sensitive_data)

        if 'ECOSYSTEM_SESSION_MANAGER_IP' not in os.environ:
            self.install_manager()
            self.manager_ip = utils.get_manager_ip(
                self.node_instances,
                manager_vm_node_id='ip',
                manager_ip_prop_key='aws_resource_id')
            self.check_manager_resources()
            os.environ['ECOSYSTEM_SESSION_MANAGER_IP'] = \
                self.manager_ip
        utils.initialize_cfy_profile(
            '{0} -u admin -p {1} -t default_tenant'.format(
                self.manager_ip, self.password))
        self.upload_plugins()

    def inputs(self):
        try:
            return {
                'password': os.environ['ECOSYSTEM_SESSION_PASSWORD'],
                'ec2_region_name': 'eu-central-1',
                'ec2_region_endpoint': 'ec2.eu-central-1.amazonaws.com',
                'availability_zone': 'eu-central-1b',
                'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
                'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID']
            }
        except KeyError:
            raise

    def check_aws_resource(self,
                           resource_id=None,
                           resource_type=None,
                           exists=True,
                           command=None):

        print 'Checking AWS resource args {0} {0} {0} {0}'.format(
            resource_id, resource_type, exists, command)

        if not isinstance(resource_id, basestring):
            print 'Warning resource_id is {0}'.format(resource_id)
            resource_id = str(resource_id)

        if command:
            pass
        elif 'cloudify.nodes.aws.ec2.Vpc' == \
                resource_type or resource_id.startswith('vpc-'):
            command = 'aws ec2 describe-vpcs --vpc-ids {0}'.format(resource_id)
        elif 'cloudify.nodes.aws.ec2.InternetGateway' == \
                resource_type or resource_id.startswith('igw-'):
            command = 'aws ec2 describe-internet-gateways ' \
                      '--internet-gateway-ids {0}'.format(resource_id)
        elif 'cloudify.nodes.aws.ec2.Subnet' == \
                resource_type or resource_id.startswith('subnet-'):
            command = 'aws ec2 describe-subnets --subnet-ids {0}'.format(
                resource_id)
        elif 'cloudify.nodes.aws.ec2.RouteTable' == \
                resource_type or resource_id.startswith('rtb-'):
            command = \
                'aws ec2 describe-route-tables --route-table-ids {0}'.format(
                    resource_id)
        elif 'cloudify.nodes.aws.ec2.NATGateway' == \
                resource_type or resource_id.startswith('nat-'):
            command = \
                'aws ec2 describe-nat-gateways --nat-gateway-ids {0}'.format(
                    resource_id)
        elif 'cloudify.nodes.aws.ec2.ElasticIP' == \
                resource_type or \
                re.compile(IP_ADDRESS_REGEX).match(resource_id):
            command = 'aws ec2 describe-addresses --public-ips {0}'.format(
                resource_id)
        elif 'cloudify.nodes.aws.ec2.SecurityGroup' == \
                resource_type or resource_id.startswith('sg-'):
            command = \
                'aws ec2 describe-security-groups --group-ids {0}'.format(
                    resource_id)
        elif 'cloudify.nodes.aws.ec2.Interface' == \
                resource_type or resource_id.startswith('eni-'):
            command = 'aws ec2 describe-network-interfaces ' \
                      '--network-interface-ids {0}'.format(
                          resource_id)
        elif 'cloudify.nodes.aws.ec2.EBSVolume' == \
                resource_type or resource_id.startswith('vol-'):
            command = 'aws ec2 describe-volumes --volume-ids {0}'.format(
                resource_id)
        elif 'cloudify.nodes.aws.ec2.Instances' == \
                resource_type or resource_id.startswith('i-'):
            command = 'aws ec2 describe-instances --instance-ids {0}'.format(
                resource_id)
        elif 'cloudify.nodes.aws.ec2.NATGateway' == \
                resource_type or resource_id.startswith('nat-'):
            command = \
                'aws ec2 describe-nat-gateways ' \
                '--nat-gateway-ids {0}'.format(resource_id)
        elif 'cloudify.nodes.aws.SQS.Queue' == resource_type:
            # Change queue url to name to get queue url.
            resource_id = resource_id.split('/')[-1]
            command = 'aws sqs get-queue-url --queue-name {0}'.format(
                resource_id)
        elif 'cloudify.nodes.aws.SNS.Topic' == resource_type:
            command = 'aws sns list-subscriptions-by-topic ' \
                      '--topic-arn {0}'.format(resource_id)
        elif 'cloudify.nodes.aws.s3.Bucket' == resource_type:
            command = 'aws s3 ls {0}'.format(resource_id)
        elif 'cloudify.nodes.aws.autoscaling.Group' == resource_type:
            command = 'aws autoscaling describe-auto-scaling-groups ' \
                      '--auto-scaling-group-names {0}'.format(resource_id)
        elif 'cloudify.nodes.aws.elb.Classic.LoadBalancer' == \
                resource_type:
            command = 'aws elb describe-load-balancers ' \
                      '--load-balancer-name my-load-balancer {0}'.format(
                          resource_id)
        elif resource_id.startswith('ami-'):
            return
        else:
            raise Exception('Unsupported type {0} for {1}.'.format(
                resource_type, resource_id))
        self.assertEqual(0 if exists else 255, utils.execute_command(command))

    def check_resources_in_deployment_created(self, nodes, node_names):
        for node in nodes:
            node_type = 'cloudify.nodes.aws.ec2.Instances' \
                if node['node_type'] == 'nodecellar.nodes.MonitoredServer' \
                else node['node_type']
            if node['id'] not in node_names:
                break
            external_id = node['instances'][0]['runtime_properties'].get(
                'aws_resource_id') if \
                'Classic.LoadBalancer' not in node_type else \
                node['instances'][0]['runtime_properties'].get(
                    'LoadBalancerName')
            if 'LifecycleHook' in node_type:
                lifecycle_hook_command = \
                    'aws autoscaling describe-lifecycle-hooks ' \
                    '--auto-scaling-group-name test-autoscaling ' \
                    '--lifecycle-hook-names {0}'.format(external_id)
                self.check_aws_resource(command=lifecycle_hook_command)
            else:
                self.check_aws_resource(external_id, node_type)

    def check_resources_in_deployment_deleted(self, nodes, node_names):
        for node in nodes:
            if node['id'] not in node_names:
                break
            node_type = 'cloudify.nodes.aws.ec2.Instances' \
                if node['node_type'] == 'nodecellar.nodes.MonitoredServer' \
                else node['node_type']
            external_id = node['instances'][0]['runtime_properties'].get(
                'aws_resource_id') if \
                'Classic.LoadBalancer' not in node_type else \
                node['instances'][0]['runtime_properties'].get(
                    'LoadBalancerName')
            if 'LifecycleHook' in node_type:
                lifecycle_hook_command = \
                    'aws autoscaling describe-lifecycle-hooks ' \
                    '--auto-scaling-group-name test-autoscaling ' \
                    '--lifecycle-hook-names {0}'.format(external_id)
                self.check_aws_resource(
                    command=lifecycle_hook_command, exists=False)
            else:
                self.check_aws_resource(external_id, node_type, exists=False)

    def check_manager_resources(self):
        for resource in utils.get_resource_ids_by_type(
                self.node_instances,
                NODE_TYPE_PREFIX,
                self.cfy_local.storage.get_node,
                id_property='aws_resource_id'):
            self.check_aws_resource(resource_id=resource)

    def upload_plugins(self):
        utils.update_plugin_yaml(
            os.environ['CIRCLE_SHA1'], 'awssdk')
        workspace_path = os.path.join(
            os.path.abspath('workspace'),
            'build')
        utils.upload_plugin(utils.get_wagon_path(workspace_path))
        for plugin in self.plugins_to_upload:
            utils.upload_plugin(plugin[0], plugin[1])

    def cleanup_deployment(self, deployment_id):
        # This is just for cleanup.
        # Because its in the lab, don't care if it passes or fails.
        utils.execute_command(
            'cfy uninstall -p ignore_failure=true {0}'.format(
                deployment_id))

    def check_nodecellar(self):
        aws_nodes = [
            'security_group',
            'haproxy_nic',
            'nodejs_nic',
            'mongo_nic',
            'nodecellar_ip'
        ]
        monitored_nodes = [
            'haproxy_frontend_host',
            'nodejs_host',
            'mongod_host'
        ]
        failed = utils.install_nodecellar(
            blueprint_file_name=self.blueprint_file_name)
        if failed:
            raise Exception('Nodecellar install failed.')
        del failed
        self.addCleanup(self.cleanup_deployment, 'nc')
        failed = utils.execute_scale(
            'nc', scalable_entity_name='nodejs_group')
        if failed:
            raise Exception('Nodecellar scale failed.')
        del failed
        deployment_nodes = \
            utils.get_deployment_resources_by_node_type_substring(
                'nc', 'cloudify')
        self.check_resources_in_deployment_created(
            deployment_nodes, aws_nodes)
        self.check_resources_in_deployment_created(
            deployment_nodes, monitored_nodes)
        blueprint_dir = tempfile.mkdtemp()
        blueprint_zip = os.path.join(blueprint_dir, 'blueprint.zip')
        blueprint_archive = 'nodecellar-auto-scale-auto-heal-blueprint-master'
        download_path = \
            os.path.join(blueprint_dir, blueprint_archive, 'aws.yaml')
        blueprint_path = utils.create_blueprint(
            utils.NODECELLAR, blueprint_zip, blueprint_dir, download_path)
        skip_transform = [
            'aws',
            'vpc',
            'public_subnet',
            'private_subnet', 
            'ubuntu_trusty_ami'
        ]
        new_blueprint_path = utils.create_external_resource_blueprint(
            blueprint_path,
            aws_nodes,
            deployment_nodes,
            resource_id_attr='aws_resource_id',
            nodes_to_keep_without_transform=skip_transform)
        failed = utils.execute_command(
            'cfy install {0} -b nc-external'.format(new_blueprint_path))
        if failed:
            raise Exception('Nodecellar external install failed.')
        failed = utils.execute_uninstall('nc-external')
        if failed:
            raise Exception('Nodecellar external uninstall failed.')
        failed = utils.execute_uninstall('nc')
        if failed:
            raise Exception('Nodecellar uninstall failed.')
        del failed
        self.check_resources_in_deployment_deleted(
            deployment_nodes, aws_nodes)
        self.check_resources_in_deployment_deleted(
            deployment_nodes, monitored_nodes)

    def network_deployment(self):
        # Create a list of node templates to verify.
        aws_nodes = [
            'nat_gateway',
            'nat_gateway_ip',
            'private_subnet_routetable',
            'public_subnet_routetable',
            'private_subnet',
            'public_subnet',
            'internet_gateway',
            'vpc'
        ]
        self.addCleanup(self.cleanup_deployment, 'aws-example-network')
        # Create Deployment (Blueprint already uploaded.)
        if utils.create_deployment('aws-example-network'):
            raise Exception(
                'Deployment aws-example-network failed.')
        # Install Deployment.
        if utils.execute_install('aws-example-network'):
            raise Exception(
                'Install aws-example-network failed.')
        # Get list of nodes in the deployment.
        deployment_nodes = \
            utils.get_deployment_resources_by_node_type_substring(
                'aws', NODE_TYPE_PREFIX)
        # Check that the nodes really exist.
        self.check_resources_in_deployment_created(
            deployment_nodes, aws_nodes)
        self.check_nodecellar()
        # Uninstall this deployment.
        if utils.execute_uninstall('aws-example-network'):
            raise Exception('Uninstall aws-example-network failed.')
        # Check that the nodes no longer exist.
        self.check_resources_in_deployment_deleted(
            deployment_nodes,
            aws_nodes)

    def check_autoscaling(self):
        blueprint_path = 'examples/autoscaling-feature-demo/test.yaml'
        blueprint_id = 'autoscaling-{0}'.format(
            os.environ['TEST_APPLICATION_PREFIX'])
        self.addCleanup(self.cleanup_deployment, blueprint_id)
        autoscaling_nodes = ['autoscaling_group']
        utils.check_deployment(
            blueprint_path,
            blueprint_id,
            NODE_TYPE_PREFIX,
            autoscaling_nodes,
            self.check_resources_in_deployment_created,
            self.check_resources_in_deployment_deleted
        )

    def check_s3(self):
        blueprint_path = 'examples/s3-feature-demo/blueprint.yaml'
        blueprint_id = 's3-{0}'.format(os.environ['TEST_APPLICATION_PREFIX'])
        self.addCleanup(self.cleanup_deployment, blueprint_id)
        s3_nodes = ['bucket']
        utils.check_deployment(
            blueprint_path,
            blueprint_id,
            NODE_TYPE_PREFIX,
            s3_nodes,
            self.check_resources_in_deployment_created,
            self.check_resources_in_deployment_deleted
        )

    def check_sqs_sns(self):
        blueprint_path = 'examples/sns-feature-demo/blueprint.yaml'
        blueprint_id = 'sqs-{0}'.format(
            os.environ['TEST_APPLICATION_PREFIX'])
        self.addCleanup(self.cleanup_deployment, blueprint_id)
        sns_nodes = ['queue', 'topic']
        utils.check_deployment(
            blueprint_path,
            blueprint_id,
            NODE_TYPE_PREFIX,
            sns_nodes,
            self.check_resources_in_deployment_created,
            self.check_resources_in_deployment_deleted
        )

    def check_load_balancing(self):
        blueprint_path = 'examples/elb-feature-demo/blueprint.yaml'
        blueprint_id = 'elb-classic-{0}'.format(
            os.environ['TEST_APPLICATION_PREFIX'])
        self.addCleanup(self.cleanup_deployment, blueprint_id)
        load_balancer_nodes = ['classic_elb']
        utils.check_deployment(
            blueprint_path,
            blueprint_id,
            NODE_TYPE_PREFIX,
            load_balancer_nodes,
            self.check_resources_in_deployment_created,
            self.check_resources_in_deployment_deleted
        )

    def deployments(self):
        self.network_deployment()
        self.check_autoscaling()
        self.check_s3()
        self.check_sqs_sns()
        # TODO: Fix too few zones in eu-central-1 issue.
        # self.check_load_balancing()
        # TODO: Add other blueprint examples for tests.

    def test_run_tests(self):
        self.deployments()
