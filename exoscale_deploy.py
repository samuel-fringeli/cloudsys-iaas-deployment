# must have env variables EXOSCALE_API_KEY and EXOSCALE_API_SECRET to work

import exoscale
exo = exoscale.Exoscale()


def cm(cmd):
    return '''#cloud-config
runcmd:
 - {cmd}
'''.format(cmd=cmd)


gva2 = exo.compute.get_zone("ch-gva-2")
micro_type = exo.compute.get_instance_type("micro")
tiny_type = exo.compute.get_instance_type("tiny")

templates = list(exo.compute.list_instance_templates(zone=gva2, name="Exoscale Container-Optimized Instance"))
sg_db = exo.compute.get_security_group(name='cloudsys_db_security')
sg_server = exo.compute.get_security_group(name='cloudsys_server_security')
docker_template = templates[0]

print('Beginning deployment to exoscale cloud...')

db_instance = exo.compute.create_instance(
    name="db", zone=gva2, type=tiny_type, template=docker_template, volume_size=15, security_groups=[sg_db],
    user_data=cm('docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root samuelfringeli/samf-appstore-db'),
)
db_ip = db_instance.ipv4_address
print('DB deployed to {ip}'.format(ip=db_ip))

backend_instance = exo.compute.create_instance(
    name="backend", zone=gva2, type=micro_type, template=docker_template, volume_size=15, security_groups=[sg_server],
    user_data=cm('docker run -p 80:8082 -e DB_HOST={ip} samuelfringeli/samf-appstore-backend'.format(ip=db_ip)),
)
backend_ip = backend_instance.ipv4_address
print('Backend deployed to {ip}'.format(ip=backend_ip))

frontend_instance = exo.compute.create_instance(
    name="frontend", zone=gva2, type=micro_type, template=docker_template, volume_size=15, security_groups=[sg_server],
    user_data=cm('docker run -p 80:80 -e BACKENDHOST={ip} samuelfringeli/samf-appstore-frontend'.format(ip=backend_ip)),
)
frontend_ip = frontend_instance.ipv4_address
print('Frontend deployed to {ip}'.format(ip=frontend_ip))

print('Please wait for a while for the frontend to be accessible.')
