# coding: utf-8
# OCI Private IP Collection Tool
# - Description: Try to collect all private IP addresses in OCI tenancy
# - Version 1.0.0
# - Date 2022.11.04
# - Author Tam Tan
# - API docs: https://docs.oracle.com/en-us/iaas/api/

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

# Begin to define a function to check if ignore or not the passed compartment
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
# end the func definition

# Begin to define a function to check if ignore or not on the passed vcn or subnet displayName
def isIgnoreCheckByDisplayName(checkList, displayName):
    ignore = False
    # Start to check on assiged compartment list
    if checkList:
        if displayName not in checkList:
            ignore = True
            
        for chkName in checkList:
            if displayName.count(chkName) > 0:
                ignore = False
                break
        # End to check on assiged compartment list
        
    return ignore
# end the func definition

# Begin to define a function to check if ignore or not on the passed vcn or subnet displayName
def isIgnoreCheckByCidrBlock(checkList, cidrBlock):
    ignore = False
    # Start to check on assiged compartment list
    if checkList:
        if cidrBlock not in checkList:
            ignore = True
        
    return ignore
# end the func definition

# Begin to define a function to check if ignore or not on the passed vcn or subnet displayName
def isIgnoreCheckByCidrBlockList(checkList, cidrBlockList):
    ignore = False
    # Start to check on assiged compartment list
    if checkList:
        # Check cidrBlockList if its CidrBlocks contains any one of checkList's CIDR
        # if contains，return True，or else False
        check = any(item in cidrBlockList for item in checkList)
        
        # If above check = false, then means it does not contain any checkList elements,
        # then need to ignore this loop
        if not check:
            ignore = True
     
    return ignore
# end the func definition

# Create a clients config list<dict>
clientConfigList = []
# Define a list to store all compartments
totalCompartments = []

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
    
    for subscribedRegion in subscribedRegionList:
        currentRegion = subscribedRegion.region_name
        clientConfig = generateClientConfig(defaultProfileUser, defaultProfileFingerprint, 
                                            defaultProfileKeyFile, defaultProfileTenancy, 
                                            currentRegion)
        clientConfigList.append(clientConfig)

## End to define initClientContext()

def collectPrviateIPs(filePath, checkRegionList, checkCompartmentList, checkVcnNameList, checkSubnetNameList, checkVcnCidrList, checkSubnetCidrList):
    privateIPsCsvFile = open(filePath, "a+")
    privateIPsCsvFile.write(f"Region, Compartment, VCN, VCN-cidr-blocks, Subnet, Subnet-cird-blocks, IP\n")

    for i, clientConfig in enumerate(clientConfigList):
        currentRegion = clientConfig["region"]
        oci.config.validate_config(clientConfig)
        
        if checkRegionList:
            if currentRegion not in checkRegionList:
                continue
        
        print(i, currentRegion)
        
        network = oci.core.VirtualNetworkClient(clientConfig)
        
        for compartment in totalCompartments:
            currentCompartmentName = compartment.fullname
            currentCompartmentId = compartment.id
            
            # ignore those compartments not in the checked list
            if isIgnoreCompartment(checkCompartmentList, compartment):
                continue  
            
            print(" => " + currentCompartmentName)

            vcns = network.list_vcns(currentCompartmentId).data
            
            if vcns:
                for vcn in vcns:
                    vcnOcid = vcn.id
                    vcnDisplayName = vcn.display_name
                    vcnIPv4CidrBlockList = vcn.cidr_blocks
                    vcnIPv6CidrBlocks = vcn.ipv6_cidr_blocks
                    vcnIPv6PrivateCidrBlocks = vcn.ipv6_private_cidr_blocks
                    vcnDomainName = vcn.vcn_domain_name
                    
                    if isIgnoreCheckByDisplayName(checkVcnNameList, vcnDisplayName):
                        continue
                    
                    if isIgnoreCheckByCidrBlockList(checkVcnCidrList, vcnIPv4CidrBlockList):
                        continue

                    vcnIPv4CidrBlocks = "|".join(vcnIPv4CidrBlockList)
                    
                    subnets = network.list_subnets(compartment_id=currentCompartmentId, vcn_id=vcnOcid).data
                    
                    if subnets:
                        print("=>---+", vcnDisplayName)
                        
                        for subnet in subnets:
                            subnetOcid = subnet.id
                            subnetDisplayName = subnet.display_name
                            subnetCidrBlock = subnet.cidr_block
                            subnetIPv6CidrBlock = subnet.ipv6_cidr_block
                            subnetIPv6CidrBlocks = subnet.ipv6_cidr_blocks
                            subnetProhibitInternetIngress = subnet.prohibit_internet_ingress
                            subnetProhibitPublicIPOnVnic = subnet.prohibit_public_ip_on_vnic
                            subnetAvailabilityDomain = subnet.availability_domain

                            if isIgnoreCheckByDisplayName(checkSubnetNameList, subnetDisplayName):
                                continue
                            
                            if isIgnoreCheckByCidrBlock(checkSubnetCidrList, subnetCidrBlock):
                                continue

                            print("=>------+", subnetDisplayName)
                            
                            ips = network.list_private_ips(subnet_id=subnetOcid).data
                            if ips:
                                for ip in ips:
                                    privateIPsCsvFile.write(f"{currentRegion},{currentCompartmentName},{vcnDisplayName},{vcnIPv4CidrBlocks},{subnetDisplayName},{subnetCidrBlock},{ip.ip_address}\n")
                                privateIPsCsvFile.flush()
                            # end if
                        # end loop subnets
                    #end if subnets
                #end loop vcns
            #end if vcns
        #end loop compartments
    #end loop regions
# end to define collectPrivateIPs func

parser = argparse.ArgumentParser(description='****  Collect OCI Private IP Information Help  ****')
parser.add_argument('--region', '-r', help='(optional) - to collect which region\'s IPs Information', nargs="*", type=str, default=[])
parser.add_argument('--compartment', '-c', help='(optional) - to collect which compartment\'s IPs Information', nargs="*", type=str, default=[])
parser.add_argument('--vname', '-vn', help='(optional) - to collect which VCN\'s private IP list by VCN Name', nargs="*", type=str, default=[])
parser.add_argument('--sname', '-sn', help='(optional) - to collect which Subnet\'s private IP list by Subnet Name', nargs="*", type=str, default=[])
parser.add_argument('--vncidr', '-vc', help='(optional) - to collect which VCN\'s private IP list by VCN CIDR Block', nargs="*", type=str, default=[])
parser.add_argument('--sncidr', '-sc', help='(optional) - to collect which Subnet\'s private IP list by Subnet CIDR Block', nargs="*", type=str, default=[])

args = parser.parse_args()


def main():
    checkRegionList = []
    checkCompartmentList = []
    checkVcnNameList = []
    checkSubnetNameList = []
    checkVcnCidrList = []
    checkSubnetCidrList = []

    dt = datetime.now()
    suffix = dt.strftime('%Y%m%d%H%M%S')
    prefix = "./private-ip-list"
    filePath = "{}_{}.csv".format(prefix, suffix)

    regionList = args.region
    if regionList:
        checkRegionList.extend(regionList)

    compartmentList = args.compartment
    if compartmentList:
        checkCompartmentList.extend(compartmentList)

    vcnNameList = args.vname
    if vcnNameList:
        checkVcnNameList.extend(vcnNameList)

    subnetNameList = args.sname
    if subnetNameList:
        checkSubnetNameList.extend(subnetNameList)

    vcnCidrList = args.vncidr
    if vcnCidrList:
        checkVcnCidrList.extend(vcnCidrList)
    
    subnetCidrList = args.sncidr
    if subnetCidrList:
        checkSubnetCidrList.extend(subnetCidrList)
    
    initClientContext()
    print("Start-to-Collect-Private-IPs...")
    collectPrviateIPs(filePath, checkRegionList, checkCompartmentList, checkVcnNameList, checkSubnetNameList, checkVcnCidrList, checkSubnetCidrList)
    print("End-to-Collect-Private-IPs!")
if __name__=="__main__":
    main()
