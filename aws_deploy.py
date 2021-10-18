import time

import boto3
import paramiko

# SSH-related
from paramiko.ssh_exception import SSHException

KEY_PATH = '/home/loic/ownCloud/master/cloudsys/labsuser.pem'
SSH_KEY = paramiko.RSAKey.from_private_key_file(KEY_PATH)
# sshClient = paramiko.SSHClient()
# sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
SSH_USER = 'ec2-user'

# AWS configuration
AWS_REGION = "us-east-1"
KEY_PAIR_NAME = 'vockey'
ec2 = boto3.resource('ec2', region_name=AWS_REGION)


# From https://maskaravivek.medium.com/how-to-ssh-into-an-ec2-instance-using-boto3-a138a4345a91
def ssh_connect_with_retry(ip_address, retries):
    if retries > 3:
        return False
    interval = 5
    sshClient = paramiko.SSHClient()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        retries += 1
        print('SSH into the instance: {}'.format(ip_address))
        sshClient.connect(hostname=ip_address, port=22,
                          username=SSH_USER, pkey=SSH_KEY, timeout=3)
        return sshClient
    except Exception as e:
        print(e)
        time.sleep(interval)
        print('Retrying SSH connection to {}'.format(ip_address))
        ssh_connect_with_retry(ip_address, retries)


def sshRunCommand(ssh, command):
    print(command)
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stdin)
        stdout.channel.set_combine_stderr(True)
        output = stdout.readlines()
        # print(output)
        # print(stdout)

    except SSHException:
        print(SSHException)
        print(stdout)
        ssh.close()
        return False
    #else:
    #    print(stdout)
    #    ssh.close()


def sshDeploy(ssh, serverRole, remoteIP):
    sshRunCommand(ssh, "sudo yum update -y")
    sshRunCommand(ssh, "sudo yum install -y docker")
    sshRunCommand(ssh, "sudo systemctl enable docker")
    sshRunCommand(ssh, "sudo systemctl start docker")

    if serverRole == 'database':
        sshRunCommand(ssh,
                      "sudo docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root samuelfringeli/samf-appstore-db")
    elif serverRole == 'backend':
        sshRunCommand(ssh,
                      "sudo docker run -d -p 80:8082 -e DB_HOST=" + remoteIP + " samuelfringeli/samf-appstore-backend")
    elif serverRole == 'frontend':
        sshRunCommand(ssh,
                      "sudo docker run -d -p 80:80 -e BACKENDHOST=" + remoteIP + " samuelfringeli/samf-appstore-frontend")


def createEc2Instance(serverRole):
    # Defining security Groups
    securityGroups = ['sg-0da65f1910c3ae00e']
    if serverRole == 'database':
        securityGroups.append('sg-0160000b3ed1e5624')
    else:
        securityGroups.append('sg-090225a02c5abea8d')

    return ec2.create_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {

                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType': 'gp2'
                },
            },
        ],
        ImageId='ami-02e136e904f3da870',
        InstanceType='t2.micro',
        MaxCount=1,
        MinCount=1,
        KeyName=KEY_PAIR_NAME,
        Monitoring={
            'Enabled': False
        },
        SecurityGroupIds=securityGroups,
    )


# Creating first EC2 instance
ec2Database = createEc2Instance('database')
ec2Backend = createEc2Instance('backend')
ec2Frontend = createEc2Instance('frontend')

# Getting ID of each instance
databaseID = ec2Database[0].id
backendID = ec2Backend[0].id
frontendID = ec2Frontend[0].id

# Waiting for IP (be sure of their creation)
ec2Database[0].wait_until_running()
time.sleep(2)
ec2Database[0].reload()
databaseIP = ec2Database[0].public_ip_address
print("Database running: " + databaseID + " at address " + databaseIP)

ec2Backend[0].wait_until_running()
time.sleep(2)
ec2Backend[0].reload()
backendIP = ec2Backend[0].public_ip_address
print("Backend running: " + backendID + " at address " + backendIP)

ec2Frontend[0].wait_until_running()
time.sleep(2)
ec2Frontend[0].reload()
frontendIP = ec2Frontend[0].public_ip_address
print("Frontend running: " + frontendID + " at address " + frontendIP)

# SSH commands
ssh1 = ssh_connect_with_retry(databaseIP, 0)
sshDeploy(ssh1, 'database', None)
ssh1.close()

ssh2 = ssh_connect_with_retry(backendIP, 0)
sshDeploy(ssh2, 'backend', databaseIP)
ssh2.close()

ssh3 = ssh_connect_with_retry(frontendIP, 0)
sshDeploy(ssh3, 'frontend', backendIP)
ssh3.close()

# Final address
print("Webapp is running: http://" + frontendIP)
