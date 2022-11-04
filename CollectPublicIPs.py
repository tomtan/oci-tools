# coding: utf-8
# OCI Public IP Collection Tool
# - Description: Try to collect all public IP information
# - Version 0.0.1
# - Date 2022.11.01
# - Author Tam Tan

from datetime import datetime
import oci
import argparse
import sys

# Deinfe a functino to generate the config dict for a secific profile
def generateClientConfig(user, fingerprint, keyfile, tenancy, region):
    clientConfig = {
        "user": user, 
        "key_file": keyfile,
        "fingerprint": fingerprint,
        "tenancy": tenancy,
        "region": region
    }
    return clientConfig

# Begin to define a entity for compartment
class CompartmentEntity:
    def __init__(self, currentId, parentId, currentName, parentName, level, fullname):
        self.level = level
        self.id = currentId
        self.pid = parentId
        self.name = currentName
        self.pname = parentName
        
        if self.level == 0:
            self.fullname = currentName
        if self.level == 1:
            self.fullname = parentName + " > " + currentName
        elif self.level >= 2:
            self.fullname = fullname + " > " + currentName
        
    def __str__(self):
        return "{'id': '%s', 'pid': '%s', 'name': '%s', 'fullname:': '%s' ,'pname': '%s','level': %s}" % (self.id, self.pid, self.name, self.fullname, self.pname, self.level)
    
# End definition

def isIgnoreCompartment(checkCompartmentList, currentCompartmentEntity):
    ignore = False
    # Start to check on assiged compartment list
    if checkCompartmentList:
        if currentCompartmentEntity.name not in checkCompartmentList:
            ignore = True
            
        for chkName in checkCompartmentList:
            if currentCompartmentEntity.fullname.count(chkName) > 0:
                ignore = False
                break
        # End to check on assiged compartment list
        
    return ignore

def enstructPublicIP(publicIp, network):
    privateIp = None
    subnetName = None
    subnetCidrBlock = None
    vcnName = None
    vcnCidrBlocks = None
    vcnCidrBlockList = None
    
    if 'PRIVATE_IP' == publicIp.assigned_entity_type:
        if publicIp.assigned_entity_id:
            privateIpBody = network.get_private_ip(private_ip_id=publicIp.assigned_entity_id).data
            privateIp = privateIpBody.ip_address
            subnet = network.get_subnet(subnet_id=privateIpBody.subnet_id).data
            subnetCidrBlock = subnet.cidr_block
            subnetName = subnet.display_name
            vcn = network.get_vcn(vcn_id=subnet.vcn_id).data
            vcnName = vcn.display_name
            vcnCidrBlockList = vcn.cidr_blocks

    elif 'NAT_GATEWAY' == publicIp.assigned_entity_type:
        if publicIp.assigned_entity_id:
            privateIpBody = network.get_nat_gateway(nat_gateway_id=publicIp.assigned_entity_id).data
            vcn = network.get_vcn(vcn_id=privateIpBody.vcn_id).data
            vcnName = vcn.display_name
            vcnCidrBlockList = vcn.cidr_blocks
    
    if vcnCidrBlockList:
        if len(vcnCidrBlockList) > 1:
            vcnCidrBlocks = " | ".join(vcnCidrBlockList)
        else:
            vcnCidrBlocks = vcnCidrBlockList[0]
    
    ociPublicIP = {
        "id": publicIp.id,
        "ip_address": publicIp.ip_address,
        "entity_type": publicIp.assigned_entity_type,
        "display_name": publicIp.display_name,
        "scope": publicIp.scope,
        "lifecycle_state": publicIp.lifecycle_state,
        "lifetime": publicIp.lifetime,
        "private_ip": privateIp,
        "subnet_name": subnetName,
        "subnet_cidr_block": subnetCidrBlock,
        "vcn_name": vcnName,
        "cidr_blocks": vcnCidrBlocks,
        "public_ip_pool_id": publicIp.public_ip_pool_id
    }
    
    return ociPublicIP
#end enstructPublicIP definition

# Define a list to store all compartments
totalCompartments = []
# Define a clients config list<dict>
clientConfigList = []

def initClientContext():
    # Init OCI context
    # Make sure that the default profile exist: ~/.oci/config [DEFAULT]
    defaultProfile="DEFAULT"

    # Load the DEFAULT profile from file: ~/.oci/config
    config = oci.config.from_file(profile_name=defaultProfile)

    # List all the DEFAULT profile parameter values
    defaultProfileUser = config["user"]
    defaultProfileFingerprint = config["fingerprint"]
    defaultProfileKeyFile = config["key_file"]
    defaultProfileTenancy = config["tenancy"]
    defaultProfileRegion = config["region"]

    # Print the DEFAULT profile parameter values
    print("#*********************[DEFAULT]*****************")
    print("user=%s" % defaultProfileUser)
    print("fingerprint=%s" % defaultProfileFingerprint)
    print("key_file=%s" % defaultProfileKeyFile)
    print("tenancy=%s" % defaultProfileTenancy)
    print("region=%s" % defaultProfileRegion)
    print("#***********************************************")

    # Init a default client via default profile
    client = oci.identity.IdentityClient(config)

    # Get all subscribed regions
    subscribedRegionList = client.list_region_subscriptions(defaultProfileTenancy).data
    print("The number of subscribed regions: ", len(subscribedRegionList))

    # Get the root compartment - Level 0
    rootCompartment = client.get_compartment(compartment_id=defaultProfileTenancy).data
    rootCompartmentEntity = CompartmentEntity(rootCompartment.id, None, rootCompartment.name, None, 0, None)

    # Get those child compartments of root compartment - Level 1
    topCompartmentPayloadList = client.list_compartments(compartment_id=defaultProfileTenancy,
                                                sort_by="NAME",sort_order="ASC",
                                            #access_level="ANY",
                                            compartment_id_in_subtree=False).data
    topCompartmentList = []
    for child in topCompartmentPayloadList:
        compartmentEntity = CompartmentEntity(child.id, rootCompartment.id, child.name, rootCompartment.name, 1, None)
        topCompartmentList.append(compartmentEntity)

    # Get sub-compartments - Level 2
    subCompartmentList = []
    for parentCompartment in topCompartmentList:
        #print("List sub-compartments of compartment: ", parentCompartment["name"])
        payload = client.list_compartments(compartment_id=parentCompartment.id)
        childList = payload.data
        
        # childList is not empty
        for child in childList:
            compartmentEntity = CompartmentEntity(child.id, parentCompartment.id, child.name, parentCompartment.name, 2, parentCompartment.fullname)
            subCompartmentList.append(compartmentEntity)

    # Get child compartments of sub-compartment - Level 3
    childSubCompartmentList = []
    for parentCompartment in subCompartmentList:
        #print("List sub-compartments of compartment: ", parentCompartment["name"])
        payload = client.list_compartments(compartment_id=parentCompartment.id)
        childList = payload.data
        # childList is not empty
        for child in childList:
            compartmentEntity = CompartmentEntity(child.id, parentCompartment.id, child.name, parentCompartment.name, 3, parentCompartment.fullname)
            childSubCompartmentList.append(compartmentEntity)

    # Get grand child compartments of child-sub-compartment - Level 4
    grandChildSubCompartmentList = []
    for parentCompartment in childSubCompartmentList:
        #print("List sub-compartments of compartment: ", parentCompartment["name"])
        payload = client.list_compartments(compartment_id=parentCompartment.id)
        childList = payload.data
        # childList is not empty
        for child in childList:
            compartmentEntity = CompartmentEntity(child.id, parentCompartment.id, child.name, parentCompartment.name, 4, parentCompartment.fullname)
            grandChildSubCompartmentList.append(compartmentEntity)

    # Get grand child compartments of grand-child-sub-compartment - Level 5
    fifthGrandChildSubCompartmentList = []
    for parentCompartment in grandChildSubCompartmentList:
        #print("List sub-compartments of compartment: ", parentCompartment["name"])
        payload = client.list_compartments(compartment_id=parentCompartment.id)
        childList = payload.data
        # childList is not empty
        for child in childList:
            compartmentEntity = CompartmentEntity(child.id, parentCompartment.id, child.name, parentCompartment.name, 5, parentCompartment.fullname)
            fifthGrandChildSubCompartmentList.append(compartmentEntity)

    # Append the root compartment to list
    totalCompartments.append(rootCompartmentEntity)
    totalCompartments.extend(topCompartmentList)
    totalCompartments.extend(subCompartmentList)
    totalCompartments.extend(childSubCompartmentList)
    totalCompartments.extend(grandChildSubCompartmentList)
    totalCompartments.extend(fifthGrandChildSubCompartmentList)

    print("The number of compartments: ", len(totalCompartments))
    # print(totalCompartments)
    print("#***********************************************")
        
    # Create a clients config list<dict>
    for subscribedRegion in subscribedRegionList:
        currentRegion = subscribedRegion.region_name
        clientConfig = generateClientConfig(defaultProfileUser, defaultProfileFingerprint, 
                                            defaultProfileKeyFile, defaultProfileTenancy, 
                                            currentRegion)
        clientConfigList.append(clientConfig)

    ##end for
##end initClientContext

def collectPublicIPs(filePath, checkCompartmentList):
    print("Start-To-Collect-Public-IPs!")

    publicIpListCsvFile = open(filePath, "a+")
    publicIpListCsvFile.write(f"ip_address,region,compartment,entity_type,lifecycle_state,lifetime,scope,vcn_name,cidr_blocks\n")
    
    for i, clientConfig in enumerate(clientConfigList):
        currentRegion = clientConfig["region"]
        oci.config.validate_config(clientConfig)
        
        #if currentRegion != 'ap-chuncheon-1':
        #    continue
        
        print(i, currentRegion)
        
        network = oci.core.VirtualNetworkClient(clientConfig)
        identity = oci.identity.IdentityClient(clientConfig)
        
        for compartment in totalCompartments:
            currentCompartmentName = compartment.fullname
            currentCompartmentId = compartment.id
            
            # ignore those compartments not in the checked list
            if isIgnoreCompartment(checkCompartmentList, compartment):
                continue  
            # print(" => " + currentCompartmentName)
            availabilityDomains = identity.list_availability_domains(compartment_id=currentCompartmentId).data
            if availabilityDomains:
                for ad in availabilityDomains:
                    adPublicIPs = network.list_public_ips(scope='AVAILABILITY_DOMAIN',availability_domain=ad.name,compartment_id=currentCompartmentId).data
                    for publicIp in adPublicIPs:
                        ociPublicIP = enstructPublicIP(publicIp, network)
                        publicIpListCsvFile.write(f"{ociPublicIP['ip_address']},{currentRegion},{currentCompartmentName},{ociPublicIP['entity_type']},{ociPublicIP['lifecycle_state']},{ociPublicIP['lifetime']},AD,{ociPublicIP['vcn_name']},{ociPublicIP['cidr_blocks']}\n")
                        publicIpListCsvFile.flush()
                    # end for loop
                #end for loop
            # end if
            
            regionPublicIPs = network.list_public_ips(scope='REGION',compartment_id=currentCompartmentId).data
            if regionPublicIPs:
                for publicIp in regionPublicIPs:
                    ociPublicIP = enstructPublicIP(publicIp, network)
                    publicIpListCsvFile.write(f"{ociPublicIP['ip_address']},{currentRegion},{currentCompartmentName},{ociPublicIP['entity_type']},{ociPublicIP['lifecycle_state']},{ociPublicIP['lifetime']},Region,{ociPublicIP['vcn_name']},{ociPublicIP['cidr_blocks']}\n")
                    publicIpListCsvFile.flush()
                # end for loop
            # end if
        #end for
    publicIpListCsvFile.close()
    print("End-To-Collect-Public-IPs!")
    # end query

parser = argparse.ArgumentParser(description='****  Collect OCI Public IP Information Help  ****')
parser.add_argument('--compartment', '-c', help='(optional) - to collect which compartment\'s IPs Information', nargs="*", type=str, default=[])
args = parser.parse_args()

def main():
    checkCompartmentList = []

    dt = datetime.now()
    suffix = dt.strftime('%Y%m%d%H%M%S')
    prefix = "./public-ip-list"
    filePath = "{}_{}.csv".format(prefix, suffix)

    compartmentList = args.compartment
    if compartmentList:
        checkCompartmentList.extend(compartmentList)

    initClientContext()
    collectPublicIPs(filePath, checkCompartmentList)

if __name__=="__main__":
    main()

