import googleapiclient.discovery
import os
import time

compute = googleapiclient.discovery.build('compute', 'v1')

print('Creating instances!')

project="western-plate-326708"
zone="europe-west6-a"


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)

def create_instance(compute, project, zone, name, bucket,scriptname):
    # Get the latest Debian Jessie image.
    image_response = compute.images().getFromFamily(
        project='debian-cloud', family='debian-9').execute()
    source_disk_image = image_response['selfLink']

    # Configure the machine
    machine_type = "zones/%s/machineTypes/n1-standard-1" % zone
    startup_script = open(
        os.path.join(
            os.path.dirname(__file__), scriptname), 'r').read()
    image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
    image_caption = "Ready for dessert?"

    config = {
        'name': name,
        'machineType': machine_type,

        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [{
                # Startup script is automatically executed by the
                # instance upon startup.
                'key': 'startup-script',
                'value': startup_script
            }, {
                'key': 'url',
                'value': image_url
            }, {
                'key': 'text',
                'value': image_caption
            }, {
                'key': 'bucket',
                'value': bucket
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()






# Creation d'instances

#création bd
print ("Create database...")
operation = create_instance(compute, project, zone, "database001", "database001", "createdb.sh")
wait_for_operation(compute, project, zone, operation['name'])
time.sleep(60)

#création backend
print ("create backend...")
operation = create_instance(compute, project, zone, "backend001", "backend001", "createbe.sh")
wait_for_operation(compute, project, zone, operation['name'])
time.sleep(60)

#création frontend
print ("create frontend...")
operation = create_instance(compute, project, zone, "frontend001", "frontend001", "createfe.sh")
wait_for_operation(compute, project, zone, operation['name'])

instances = list_instances(compute, project, zone)

print('Instances in project %s and zone %s:' % (project, zone))

for instance in instances:
    for interface in instance['networkInterfaces']:
        print (instance ['name'] + ", privateIp:" + interface['networkIP'] + ", publicIp:" + interface['accessConfigs'][0]['natIP'])
            
