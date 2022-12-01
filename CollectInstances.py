#coding: utf-8
# OCI Instance Information Collection Tool
# - Description: Try to collect all instances information(including Compute/Autonomouse DB/DBCS/MySQL instances)
# - Version 0.0.2
# - Date 2022.10.27
# - Author: Tam Tan

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

# Define a list to store all compartments
totalCompartments = []
# Define a clients config list<dict>
clientConfigList = []

def initClientContext():
    # Init OCI context
    # Make sure that the default profile exist: ./oci/config [DEFAULT]
    defaultProfile="DEFAULT"

    # Load the DEFAULT profile from file: ./oci/config
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
        
    # Begin to create a clients config list<dict>
    for subscribedRegion in subscribedRegionList:
        currentRegion = subscribedRegion.region_name
        clientConfig = generateClientConfig(defaultProfileUser, defaultProfileFingerprint, 
                                            defaultProfileKeyFile, defaultProfileTenancy, 
                                            currentRegion)
        clientConfigList.append(clientConfig)

    ## End to create a clients config list<dict>

def collectComputeInstances(clientConfigList, chckCompartmentList, suffix):
    print("Start-To-Collect-Compute-Instances...")
    # Define a csv file to store instances list
    prefix = "./compute-instances"
    filePath = "{}_{}.csv".format(prefix, suffix)
    instancesCsvFile = open(filePath, "a+")

    instancesCsvFile.write(f"Name, Status, OCPUs, RAM(GBs),Shape, Boot Volume, Block Volumes, Compartment, Region, Public IPs, Private IPs\n")
    # Loop every client config then 
    for clientConfig in clientConfigList:
        currentRegion = clientConfig["region"]
        oci.config.validate_config(clientConfig)

        print("I'm here >>> ", currentRegion)
        
        #config = oci.config.from_file(profile_name=defaultProfile)
        computeClient = oci.core.ComputeClient(clientConfig)
        blockStorageClient = oci.core.BlockstorageClient(clientConfig)
        networkClient = oci.core.VirtualNetworkClient(clientConfig)

        for compartment in totalCompartments:
            currentCompartmentName = compartment.fullname
            currentCompartmentId = compartment.id
            
            # ignore those compartments not in the checked list
            if isIgnoreCompartment(chckCompartmentList, compartment):
                continue
            
            instancesResponse = computeClient.list_instances(currentCompartmentId)
            instanceList = instancesResponse.data
            #print("Region: {}, Compartment: {}, Number of Instances: {}".format(currentRegion, currentCompartmentName, len(instanceList)))
            for instance in instanceList:
                #print(instance)
                instanceId = instance.id
                instanceAd = instance.availability_domain

                bootVolumeDesc = ""
                bootVolumes = computeClient.list_boot_volume_attachments(availability_domain=instanceAd,compartment_id=currentCompartmentId,instance_id=instanceId).data
                if bootVolumes:
                    bvId = bootVolumes[0].boot_volume_id
                    try:
                        bootVolume = blockStorageClient.get_boot_volume(boot_volume_id=bvId).data
                        bootVolumeSize = bootVolume.size_in_gbs 
                        bootVolumeVPUs = bootVolume.vpus_per_gb
                        bootVolumeDesc = "{}(gb)-{}(pu)".format(bootVolumeSize, bootVolumeVPUs)
                    except:
                        print(">>>BootVolume Error:", bootVolumes)

                blockVolumeList = []
                blockVolumes = computeClient.list_volume_attachments(availability_domain=instanceAd,compartment_id=currentCompartmentId,instance_id=instanceId).data
                if blockVolumes:
                    for blv in blockVolumes:
                        #print(blv)
                        volumeId = blv.volume_id
                        try:
                            blockVolume = None
                            if volumeId.count('bootvolume') > 0:
                                blockVolume = blockStorageClient.get_boot_volume(boot_volume_id=volumeId).data
                            else:
                                blockVolume = blockStorageClient.get_volume(volume_id=volumeId).data

                            if blockVolume:
                                blockVolumeSize = blockVolume.size_in_gbs 
                                blockVolumeVPUs = blockVolume.vpus_per_gb
                                blockVolumeDesc = "{}(gb)-{}(pu)".format(blockVolumeSize, blockVolumeVPUs)
                                blockVolumeList.append(blockVolumeDesc)
                        except:
                            print(">>>Error in BlockVolume [ %s ]" % volumeId)
                
                blockVolumes = ""
                if blockVolumeList:
                    if len(blockVolumeList) == 1:
                        blockVolumes = blockVolumeList[0]
                    else:
                        blockVolumes = " & ".join(blockVolumeList)
                
                publicIpList = []
                privateIpList = []
                vnicAttachList = computeClient.list_vnic_attachments(compartment_id=currentCompartmentId,availability_domain=instanceAd,instance_id=instanceId).data
                if vnicAttachList:
                    for vnicAttach in vnicAttachList:
                        vnic = networkClient.get_vnic(vnic_id=vnicAttach.vnic_id).data
                        pubIp = vnic.public_ip
                        priIp = vnic.private_ip
                        if pubIp:
                            publicIpList.append(pubIp)
                        if priIp:
                            privateIpList.append(priIp)
                
                publicIPs = ""
                if publicIpList:
                    if len(publicIpList) == 1:
                        publicIPs = publicIpList[0]
                    else:
                        publicIPs = " | ".join(publicIpList)
                
                privateIPs = ""
                if privateIpList:
                    if len(privateIpList) == 1:
                        privateIPs = privateIpList[0]
                    else:
                        privateIPs = " | ".join(privateIpList)

                state = instance.lifecycle_state
                displayName = instance.display_name
                shapeConfig = instance.shape_config
                ocpus = shapeConfig.ocpus
                ram = shapeConfig.memory_in_gbs
                shape = instance.shape
                instancesCsvFile.write(f"{displayName},{state},{ocpus},{ram},{shape},{bootVolumeDesc},{blockVolumes},{currentCompartmentName},{currentRegion},{publicIPs},{privateIPs}\n")
                instancesCsvFile.flush()
            
    # close csv file
    instancesCsvFile.close()
    print("End-To-Collect-Compute-Instances!")

def collectAdbInstances(clientConfigList, chckCompartmentList, suffix):
    print("Start-To-Collect-Autonomouse-Databases...")
    # Define a csv file to store instances list
    prefix = "./adb-instances"
    filePath = "{}_{}.csv".format(prefix, suffix)
    instancesCsvFile = open(filePath, "a+")

    instancesCsvFile.write(f"Name, Status, OCPUs, Storage, Workload, Version, Compartment, Region\n")
    # Loop every client config then 
    for clientConfig in clientConfigList:
        currentRegion = clientConfig["region"]
        oci.config.validate_config(clientConfig)

        print("I'm here >>> ", currentRegion)
        
        #config = oci.config.from_file(profile_name=defaultProfile)
        databaseClient = oci.database.DatabaseClient(clientConfig)
        
        for compartment in totalCompartments:
            currentCompartmentName = compartment.fullname
            currentCompartmentId = compartment.id
            
            # ignore those compartments not in the checked list
            if isIgnoreCompartment(chckCompartmentList, compartment):
                continue
            
            
            # Query all Autonomous Databases
            adbResponse = databaseClient.list_autonomous_databases(compartment_id=currentCompartmentId)
            adbList = adbResponse.data
            
            # print("Region: {}, Compartment: {}, Number of Autonomous DB: {}".format(currentRegion, currentCompartmentName, len(adbList)))
            
            for instance in adbList:
                # print(instance)
                state = instance.lifecycle_state
                displayName = instance.display_name
                ocpus = instance.cpu_core_count
                storage = instance.data_storage_size_in_gbs
                workload = instance.db_workload
                version = instance.db_version
                # print(displayName, int(ocpus), int(storage), state)
                instancesCsvFile.write(f"{displayName},{state},{ocpus},{storage},{workload},{version},{currentCompartmentName},{currentRegion}\n")
                instancesCsvFile.flush()
            
    # close csv file
    instancesCsvFile.close()
    print("End-To-Collect-Autonomouse-Databases!")

def collectDBCSInstances(clientConfigList, chckCompartmentList, suffix):
    print("Start-To-Collect-DBCS-Instances...")
    # Define a csv file to store instances list
    prefix = "./dbcs-instances"
    filePath = "{}_{}.csv".format(prefix, suffix)
    instancesCsvFile = open(filePath, "a+")

    instancesCsvFile.write(f"Name, Status, OCPUs, Storage, Shape, Edition, Version, Compartment, Region\n")
    # Loop every client config then 
    for clientConfig in clientConfigList:
        currentRegion = clientConfig["region"]
        oci.config.validate_config(clientConfig)

        print("I'm here >>> ", currentRegion)
        
        #config = oci.config.from_file(profile_name=defaultProfile)
        databaseClient = oci.database.DatabaseClient(clientConfig)
        
        for compartment in totalCompartments:
            currentCompartmentName = compartment.fullname
            currentCompartmentId = compartment.id
            
            # ignore those compartments not in the checked list
            if isIgnoreCompartment(chckCompartmentList, compartment):
                continue
            
            # Query all Managed Databases
            databasesResponse = databaseClient.list_db_systems(compartment_id=currentCompartmentId)
            dbInstanceList = databasesResponse.data
            #print(dbInstanceList)
            
            # print("Region: {}, Compartment: {}, Number of DBCS: {}".format(currentRegion, currentCompartmentName, len(dbInstanceList)))
            
            for instance in dbInstanceList:
                #print(instance)
                displayName = instance.display_name
                state = instance.lifecycle_state
                ocpus = instance.cpu_core_count
                storage = instance.data_storage_size_in_gbs
                shape = instance.shape
                edition = instance.database_edition
                version = instance.version
                instancesCsvFile.write(f"{displayName},{state},{ocpus},{storage},{shape},{edition},{version},{currentCompartmentName},{currentRegion}\n")
                instancesCsvFile.flush()
            
    # close csv file
    instancesCsvFile.close()
    print("End-To-Collect-DBCS-Instances!")

def collectMySQLInstances(clientConfigList, chckCompartmentList, suffix):
    print("Start-To-Collect-MySQL-Instances...")
    prefix = "./mysql-instances"
    filePath = "{}_{}.csv".format(prefix, suffix)
    instancesCsvFile = open(filePath, "a+")

    instancesCsvFile.write(f"Name, Status, OCPUs, RAM(GBs), Shape, Version, IsHA, Compartment, Region\n")
    # Loop every client config then 
    for clientConfig in clientConfigList:
        currentRegion = clientConfig["region"]
        oci.config.validate_config(clientConfig)

        print("I'm here >>> ", currentRegion)
        
        #config = oci.config.from_file(profile_name=defaultProfile)
        mysqlClient = oci.mysql.DbSystemClient(clientConfig)
        mysqlIaaSClient = oci.mysql.MysqlaasClient(clientConfig)
        
        for compartment in totalCompartments:
            currentCompartmentName = compartment.fullname
            currentCompartmentId = compartment.id
            
            # ignore those compartments not in the checked list
            if isIgnoreCompartment(chckCompartmentList, compartment):
                continue
            
            # Query all Managed Databases
            mysqlResponse = mysqlClient.list_db_systems(compartment_id=currentCompartmentId,lifecycle_state='ACTIVE')
            mysqlList = mysqlResponse.data
            
            #print("Region: {}, Compartment: {}, Number of MySQL: {}".format(currentRegion, currentCompartmentName, len(mysqlList)))
            
            for instance in mysqlList:
                displayName = instance.display_name
                state = instance.lifecycle_state
                shapeName = instance.shape_name
                mysqlShapeInfo = mysqlIaaSClient.list_shapes(compartment_id=currentCompartmentId,name=shapeName).data[0]
                ocpus = mysqlShapeInfo.cpu_core_count
                ram = mysqlShapeInfo.memory_size_in_gbs
                version = instance.mysql_version
                isHA = instance.is_highly_available
                instancesCsvFile.write(f"{displayName},{state},{ocpus},{ram},{shapeName},{version},{isHA},{currentCompartmentName},{currentRegion}\n")
                instancesCsvFile.flush()
            
    # close csv file
    instancesCsvFile.close()
    print("End-To-Collect-MySQL-Instances!")

allowedParameterValues = ['ci', 'ai', 'di', 'mi', 'ti']
parser = argparse.ArgumentParser(description='****  Collect OCI Instances Information Help  ****')
parser.add_argument('--asset', '-a', help='(required) - to collect which asset. The passed value can be one of them: [\'ti\', \'ci\', \'ai\', \'mi\', \'di\']. `ci`=Compute Instance, `ai`=Automouse Instance, `mi`=MySQL Instance, `di`=DBCS Instance, `ti` means total instances.', nargs="*", required=True, type=str)
parser.add_argument('--compartment', '-c', help='(optional) - to collect which compartment name', nargs="*", type=str, default=[])

args = parser.parse_args()

def main():
    exampleCommandTips = '************************\nFor example:\n (1)`python CollectInstances.py -a ci di mi -c SPECIALLIST2`\n (2)`python CollectInstances.py -a mi`\n (3)`python CollectInstances.py -a ti`\n ************************\n Look more infomation try use `python CollectInstances.py --help`'
    
    # Generate suffix for CSV files
    dt = datetime.now()
    suffix = dt.strftime('%Y%m%d%H%M%S')
    
    # Only check those compartments you needs
    # [ 'SPECIALLIST2' ]
    chckCompartmentList = []
    
    compartmentList = args.compartment
    if compartmentList:
        chckCompartmentList.extend(compartmentList)

    assets = args.asset
    isParameterValid = True
    if assets:
        for asset in assets:
            if asset in allowedParameterValues:
                isParameterValid = isParameterValid & True
            else:
                isParameterValid = False
                break
    else:
        print(exampleCommandTips)
        sys.exit(0)
    
    if not isParameterValid:
        print(exampleCommandTips)
        sys.exit(0)
    else:
        try:
            initClientContext()
            if 'ci' in assets or 'ti' in assets:
                collectComputeInstances(clientConfigList, chckCompartmentList, suffix)
            if 'ai' in assets or 'ti' in assets:
                collectAdbInstances(clientConfigList, chckCompartmentList, suffix)
            if 'di' in assets or 'ti' in assets:
                collectDBCSInstances(clientConfigList, chckCompartmentList, suffix)
            if 'mi' in assets or 'ti' in assets:
                collectMySQLInstances(clientConfigList, chckCompartmentList, suffix)
        except Error as e:
            print("Error: " + e)

if __name__=="__main__":
    main()