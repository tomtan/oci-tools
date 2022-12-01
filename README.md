# oci-tools

## Purpose

The purpose of this Python Script(CollectInstances.py & CollectPublicIPs.py & CollectPrivateIPs.py) is trying to collect all those instances shape information and public/private IP addresses across the total regions/compartments in Oracle Cloud Infrastructure(OCI) tenancy.

## How to use these scripts

- Collect total instances information of tenancy with filtering by the compartments:

  ``python CollectInstances.py -a ti -c <compartment1> <compartment2>``
- Collect compute, mysql and dbcs intances information with filtering by the compartments:

  ``python CollectInstances.py -a ci mi di -c <compartment1> <compartment2>``
- Collect those public IP addresses of OCI tenancy with specified compartments:

  ``python CollectPublicIPs.py -c <compartment>``
- Collect those private IP addresses of OCI tenany with some specified parameters:

  ```
  # The following command is trying to collect the private IP addresses 
  # with specified Region & Compartment & VCN Display Name & Subnet CIDR Blocks.

  python CollectPrivateIPs.py -r ap-tokyo-1 -c SPECIALLIST2 -vn SDWAN -sc 10.210.0.0/24

  ```

## Command outputs:

There may output 4 csv files when run on the script `CollectInstances.py` :

> (1) compute-instances_< timestamp >.csv - for storing compute instances as following columns:

> | Name | Status | OCPUs | RAM(GBs) | Shape | Boot Volume | Block Volumes | Compartment | Region | Public IPs  |  Private IPs |

> Sample Data:
> test, TERMINATED, 1, 6, VM.Standard.A1.Flex, 47(gb)-10(pu), 100(gb)-10(pu) & 100(gb)-10(pu), A > B > C, eu-amsterdam-1

> (2) adb-instances_< timestamp >.csv - for storing Autonomous DB instances as following columns:

> Name | Status | OCPUs | Storage | Workload | Version | Compartment | Region

> Sample Data:
> DB202110190731, STOPPED, 1, 1024, DW, 19c, A > B, ap-seoul-1

> (3) dbcs-instances_< timestamp >.csv - for storing DBCS instances as following columns:

> Name | Status | OCPUs | Storage | Shape | Edition | Version | Compartment | Region

> (4) mysql-instances_< timestamp >.csv - for storing MySQL instances  as following columns:

> Name | Status | OCPUs | RAM(GBs) | Shape | Version | IsHA | Compartment| Region

> For example - mysql-instances_< timestamp >.csv, you will see the collection sample data like the following table:

| Name          | Status | OCPUs | RAM(GBs) | Shape     | Version | IsHA  | Compartment  | Region       |
| ------------- | ------ | ----- | -------- | --------- | ------- | ----- | ------------ | ------------ |
| instance-name | ACTIVE | 16    | 512      | Standard3 | 8.0.28  | FALSE | root > A > C | us-ashburn-1 |

There will output 1 csv file when run on the script `CollectPublicIPs.py`:

> (1) public-ip-list_< timestamp >.csv - for storing Public IP addresses as following columns:

> ip_address | region | compartment | entity_type | lifecycle_state | lifetime | scope | vcn_name | cidr_blocks

There will output 1 csv file when run on the script `CollectPrivateIPs.py`:

> (1) private-ip-list_< timestamp >.csv - for storing Private IP addresses as following columns:

> Region | Compartment | VCN | VCN-cidr-blocks | Subnet | Subnet-cird-blocks | IP

## Setup the running environment

(1) It can execute directly in OCI cloud shell.

(2) If you want to run these scripts in your local desktop, make sure that you have installed python3+ and oci python sdk 2.86.0.

You can check the python context environment with using command:

```
pip freeze

```

(3) After installed python & oci python sdk, then require to create a file "~/.oci/config", and its content like belows:

```
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaak.......
fingerprint=cc:aa:33:bb:dd:cc:nn:mm:ii:gg:aa:bb:bb:cc:vv:zz
key_file=/Users/tom/api-key/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..aaaaaaaa..........
region=ap-chuncheon-1
```

While use this tool it's better base on an OCI tenancy administrator, or else please make sure that the user has those permissions to read the shape information of instances. More CLI context config file settings, please see the document: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm.

(4) Try the following commands to collect those information for your tenancy.

(4.1) Command with `-h` or `--help` option is to see optional arguments.

```
  python CollectInstances.py -h
  
  optional arguments:
  -h, --help            show this help message and exit
  --asset [ASSET [ASSET ...]], -a [ASSET [ASSET ...]]
                        (required) - to collect which asset. The passed value can be one of them: ['ti', 'ci','ai', 'mi', 'di']. 
                        ci=Compute Instance, ai=Automouse Instance, mi=MySQL Instance,di=DBCS Instance, ti means total instances of the tenancy.
  --compartment [COMPARTMENT [COMPARTMENT ...]], -c [COMPARTMENT [COMPARTMENT ...]]
                        (optional) - to collect which compartment<name>.
```

(4.2) The following example commands for your reference.

| Example commands                                       | Description                                                                                                             |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| python CollectInstances.py -a ci di mi -c SPECIALLIST2 | Collect those shape infomation of compute instances, dbcs instances and mysql instances in compartment `SPECIALLIST2` |
| python CollectInstances.py -a mi                       | Collect those shape infomation of mysql instances in all regions & all compartments                                     |
| python CollectInstances.py -a ti                       | Collect those shape infomation of total instances(compute/adb/dbcs/mysql) in all regions & all compartments             |

Please feel free to use this tool. Hope it's helpful for you on OCI cloud journey.
