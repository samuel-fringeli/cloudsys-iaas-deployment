from novaclient import client
from novaclient.v2.servers import ServerManager
from novaclient.v2.images import GlanceManager
from novaclient.v2.flavors import FlavorManager
from neutronclient.v2_0 import client as neutron_client
from keystoneauth1 import loading
from keystoneauth1 import session
from time import sleep


def cm(cmd):
    return '''#cloud-config
runcmd:
 - {cmd}
'''.format(cmd=cmd)


def get_ip(instance):
    interfaces = []
    while len(interfaces) <= 0:
        interfaces = server_manager.interface_list(instance)
        sleep(1)

    return [x for x in list(interfaces[0].fixed_ips) if len(x['ip_address'].split('.')) == 4][0]['ip_address']


loader = loading.get_plugin_loader('password')
auth = loader.load_from_options(
    auth_url='https://keystone.cloud.switch.ch:5000/v3',
    username='leonard.noth@master.hes-so.ch',
    password='94d8af7f2c5b70d736f9904234bd1add',
    project_name='Fringeli_Guibert_Imbert_Noth_Vuagniaux',
    project_domain_name='Default',
    user_domain_name='Default'
)
sess = session.Session(auth=auth)
nova = client.Client('2.1', session=sess, region_name='ZH')
neutron = neutron_client.Client(session=sess)
server_manager = ServerManager(nova)
glance_manager = GlanceManager(nova)
flavor_manager = FlavorManager(nova)

floating_ips = neutron.list_floatingips()
down_floating_ips = [x for x in floating_ips['floatingips'] if x['status'] == 'DOWN']

if len(down_floating_ips) == 0:
    raise Exception('There are no down floating IPs. Please create one from the switch engine interface.')
public_ip = down_floating_ips[0]

docker_image = glance_manager.find_image('docker')
flavors = flavor_manager.list()
c1_small = [flavor for flavor in flavors if flavor.name == 'c1.small'][0]

print('Beginning deployment to switch engine cloud...')
db_instance = server_manager.create(
    name='db', image=docker_image.id, flavor=c1_small.id, security_groups=['SQL'],
    userdata=cm("docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root samuelfringeli/samf-appstore-db")
)
db_ip = get_ip(db_instance)
print('DB deployed to {ip}'.format(ip=db_ip))

backend_instance = server_manager.create(
    name='backend', image=docker_image.id, flavor=c1_small.id, security_groups=['HTTP'],
    userdata=cm("docker run -p 80:8082 -e DB_HOST={ip} samuelfringeli/samf-appstore-backend".format(ip=db_ip))
)
backend_ip = get_ip(backend_instance)
print('Backend deployed to {ip}'.format(ip=backend_ip))

frontend_instance = server_manager.create(
    name='frontend', image=docker_image.id, flavor=c1_small.id, security_groups=['HTTP'],
    userdata=cm("docker run -p 80:80 -e BACKENDHOST={ip} samuelfringeli/samf-appstore-frontend".format(ip=backend_ip))
)
frontend_ip = get_ip(frontend_instance)

# allocate public IP to frontend
frontend_interface_port = server_manager.interface_list(frontend_instance)[0].port_id
neutron.update_floatingip(public_ip['id'], { 'floatingip': {'port_id': frontend_interface_port}})
print('Frontend deployed to {ip}'.format(ip=public_ip['floating_ip_address']))

print('Please wait for a while for the frontend to be accessible.')
