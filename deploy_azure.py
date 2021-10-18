#!/usr/bin/env python3

#----------------------------------------------------------------------------------
# Author: Rémy Vuagniaux
# MSE Labo Cloud 01 
#
# This program create 3 virtual machines: a database, a backend ad a frontend
# Ones created, it configure the machines
#----------------------------------------------------------------------------------

# Import the needed credential and management objects from the libraries.
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
import os
import json

# This function is used to retreive some data from azure by using command line
# because azure python api does not support some function
def get_from_azure_by_bash_command_line_because_azure_suck(addr:str, field:str):
    stream = os.popen(command)
    output = stream.read()
    json_object = json.loads(output)
    return json_object[field]
    
# GETTING ACCOUNT CREDENTIAL
#------------------------------------------------------------

# Acquire a credential object using CLI-based authentication.
credential = AzureCliCredential()

#REPLACE WITH YOUR OWN SUBSCRIPTION ID
subscription_id = "place-your-own"

# SETTING AND GETTING THE VM PARAM
#------------------------------------------------------------

# Obtain the management object for resources, using the credentials from the CLI login.
resource_client = ResourceManagementClient(credential, subscription_id)

# Constants we need in multiple places: the resource group name and the region
# in which we provision resources. You can change these values however you want.

#REPLACE WITH YOUR OWN RESOURCE GROUP
RESOURCE_GROUP_NAME = "PW_Cloud_01"
LOCATION = "westeurope"

#REPLACE WITH YOUR OWN VNET
VNET_NAME = "PW_Cloud_01-vnet"
SUBNET_NAME = "default"

command = 'az network vnet subnet show -g ' + RESOURCE_GROUP_NAME + ' -n ' + SUBNET_NAME + ' --vnet-name ' + VNET_NAME
SUBNET_ID = get_from_azure_by_bash_command_line_because_azure_suck(command, "id")

network_client = NetworkManagementClient(credential, subscription_id)


# CREATION OF DATABASE
#---------------------------------------------------------------------
IP_NAME = "database-autodeployed-ip"
IP_CONFIG_NAME = "database-autodeployed-ip-config"
NIC_NAME = "database-autodeployed-nic"
VM_NAME = "DataBaseAutoVM"
USERNAME = "azureuser"
PASSWORD = "Pa$$w0rd"

poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    }
)

ip_address_result = poller.result()

print(f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}")

# Step 5: Provision the network interface client
poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME,
    NIC_NAME, 
    {
        "location": LOCATION,
        "ip_configurations": [ {
            "name": IP_CONFIG_NAME,
            "subnet": { "id": SUBNET_ID },
            "public_ip_address": {"id": ip_address_result.id } 
        }]
    }
)

nic_result = poller.result()

database_private_ip = nic_result.ip_configurations[0].private_ip_address
print("database private ip address: ", database_private_ip)

print(f"Provisioned network interface client {nic_result.name}")

# Step 6: Provision the virtual machine

# Obtain the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)

print(f"Provisioning virtual machine {VM_NAME}; this operation might take a few minutes.")

# Provision the VM specifying only minimal arguments, which defaults to an Ubuntu 18.04 VM
# on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.

poller = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME,
    {
        "location": LOCATION,
        "storage_profile": {
            "image_reference": {
                "publisher": 'Canonical',
                "offer": "UbuntuServer",
                "sku": "16.04.0-LTS",
                "version": "latest"
            }
        },
        "hardware_profile": {
            "vm_size": "Standard_DS1_v2"
        },
        "os_profile": {
            "computer_name": VM_NAME,
            "admin_username": USERNAME,
            "admin_password": PASSWORD
        },
        "network_profile": {
            "network_interfaces": [{
                "id": nic_result.id,
            }]
        }
    }
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")

# CREATION OF BACKEND
#---------------------------------------------------------------------
IP_NAME = "backend-autodeployed-ip"
IP_CONFIG_NAME = "backend-autodeployed-ip-config"
NIC_NAME = "backend-autodeployed-nic"
VM_NAME = "BackEndAutoVM"
USERNAME = "azureuser"
PASSWORD = "Pa$$w0rd"

poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    }
)

ip_address_result = poller.result()

print(f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}")

# Step 5: Provision the network interface client
poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME,
    NIC_NAME, 
    {
        "location": LOCATION,
        "ip_configurations": [ {
            "name": IP_CONFIG_NAME,
            "subnet": { "id": SUBNET_ID },
            "public_ip_address": {"id": ip_address_result.id } 
        }]
    }
)

nic_result = poller.result()

backend_private_ip = nic_result.ip_configurations[0].private_ip_address
print("backend private ip address: ", backend_private_ip)

print(f"Provisioned network interface client {nic_result.name}")

# Step 6: Provision the virtual machine

# Obtain the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)

print(f"Provisioning virtual machine {VM_NAME}; this operation might take a few minutes.")

# Provision the VM specifying only minimal arguments, which defaults to an Ubuntu 18.04 VM
# on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.

poller = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME,
    {
        "location": LOCATION,
        "storage_profile": {
            "image_reference": {
                "publisher": 'Canonical',
                "offer": "UbuntuServer",
                "sku": "16.04.0-LTS",
                "version": "latest"
            }
        },
        "hardware_profile": {
            "vm_size": "Standard_DS1_v2"
        },
        "os_profile": {
            "computer_name": VM_NAME,
            "admin_username": USERNAME,
            "admin_password": PASSWORD
        },
        "network_profile": {
            "network_interfaces": [{
                "id": nic_result.id,
            }]
        }
    }
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")


# CREATION OF FRONTEND
#---------------------------------------------------------------------
IP_NAME = "frontend-autodeployed-ip"
IP_CONFIG_NAME = "frontend-autodeployed-ip-config"
NIC_NAME = "frontend-autodeployed-nic"
VM_NAME = "FrontEndAutoVM"
USERNAME = "azureuser"
PASSWORD = "Pa$$w0rd"

#REPLACE WITH YOUR OWN NETWORK SECURITY GROUP
NSG_NAME = "frontEndnsg288"

command = 'az network nsg show -g ' + RESOURCE_GROUP_NAME + ' -n ' + NSG_NAME
NSG_ID = get_from_azure_by_bash_command_line_because_azure_suck(command, "id")

poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    }
)

ip_address_result = poller.result()

print(f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}")

# Step 5: Provision the network interface client
poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME,
    NIC_NAME, 
    {
        "location": LOCATION,
        "ip_configurations": [ {
            "name": IP_CONFIG_NAME,
            "subnet": { "id": SUBNET_ID },
            "public_ip_address": {"id": ip_address_result.id } 
        }],
        "network_security_group": {
        'id': NSG_ID
        }
    }
)



nic_result = poller.result()

print(f"Provisioned network interface client {nic_result.name}")

# Step 6: Provision the virtual machine

# Obtain the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)

print(f"Provisioning virtual machine {VM_NAME}; this operation might take a few minutes.")

# Provision the VM specifying only minimal arguments, which defaults to an Ubuntu 18.04 VM
# on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.

poller = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME,
    {
        "location": LOCATION,
        "storage_profile": {
            "image_reference": {
                "publisher": 'Canonical',
                "offer": "UbuntuServer",
                "sku": "16.04.0-LTS",
                "version": "latest"
            }
        },
        "hardware_profile": {
            "vm_size": "Standard_DS1_v2"
        },
        "os_profile": {
            "computer_name": VM_NAME,
            "admin_username": USERNAME,
            "admin_password": PASSWORD
        },
        "network_profile": {
            "network_interfaces": [{
                "id": nic_result.id,
            }]
        }
    }
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")

# CONFIGURATION OF THE DATABASE
#---------------------------------------------------------------------
VM_NAME = "DataBaseAutoVM"
run_command_parameters={
'command_id': 'RunShellScript',
'script': ['sudo apt-get update -y',
           'touch /home/test.txt',
           'sudo apt-get install apt-transport-https ca-certificates curl software-properties-common -y',
           'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add',
           'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu  $(lsb_release -cs)  stable" -y',
           'sudo apt update -y',
           'sudo apt-get install docker-ce -y',
           'sudo systemctl enable docker',
           'sudo docker run -d --name dataBase -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root samuelfringeli/samf-appstore-db'
          ]
}

poller = compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP_NAME,VM_NAME,run_command_parameters)
result = poller.result()
print(result.value[0].message)

# CONFIGURATION OF THE BACKEND
#---------------------------------------------------------------------
VM_NAME = "BackEndAutoVM"
run_command_parameters={
'command_id': 'RunShellScript',
'script': ['sudo apt-get update -y',
           'touch /home/test.txt',
           'sudo apt-get install apt-transport-https ca-certificates curl software-properties-common -y',
           'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add',
           'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu  $(lsb_release -cs)  stable" -y',
           'sudo apt update -y',
           'sudo apt-get install docker-ce -y',
           'sudo systemctl enable docker',
           'sudo docker run -d --name backEnd -p 80:8082 -e DB_HOST='+database_private_ip+' samuelfringeli/samf-appstore-backend'
          ]
}

poller = compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP_NAME,VM_NAME,run_command_parameters)
result = poller.result()
print(result.value[0].message)

# CONFIGURATION OF THE FRONTEND
#---------------------------------------------------------------------
VM_NAME = "FrontEndAutoVM"
run_command_parameters={
'command_id': 'RunShellScript',
'script': ['sudo apt-get update -y',
           'touch /home/test.txt',
           'sudo apt-get install apt-transport-https ca-certificates curl software-properties-common -y',
           'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add',
           'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu  $(lsb_release -cs)  stable" -y',
           'sudo apt update -y',
           'sudo apt-get install docker-ce -y',
           'sudo systemctl enable docker',
           'sudo docker run -d --name FrontEnd -p 80:80 -e "BACKENDHOST='+backend_private_ip+'" samuelfringeli/samf-appstore-frontend'
          ]
}

poller = compute_client.virtual_machines.begin_run_command(RESOURCE_GROUP_NAME,VM_NAME,run_command_parameters)
result = poller.result()
print(result.value[0].message)
