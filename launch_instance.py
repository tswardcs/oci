import oci
import argparse
import sys
import traceback


def get_tenancy_ocid():
    return ("ocid1.tenancy.oc1.." +
           "aaaaaaaa7s4zdy3dcyfxojduycq2cu6hsn2bh5l3evrwxp5uknp5e3vkelgq")


def config_setup():
    global VERBOSE
    try:
        config = oci.config.from_file()
    except oci.exceptions.ConfigFileNotFound as cfnf:
        print("oci.exceptions.ConfigFileNotFound")
        if(VERBOSE):
            print(traceback.format_exc())
        raise cfnf
    except oci.exceptions.InvalidKeyFilePath as ikfp:
        print("oci.exceptions.InvalidKeyFilePath")
        if(VERBOSE):
            print(traceback.format_exc())
        raise ikfp
    #if(VERBOSE):
    #    print(config)
    return config



def main_routine(args):
    VERBOSE=args.verbose
    ERROR_MSG = "Returning ERROR STATUS"
    cmpt_name=args.compartment_name
    icfg_name=args.instance_cfg_name
    inst_name=""
    if args.instance_name is not None:
        inst_name=args.instance_name
    #print("Launch vars: \"" + cmpt_name + "\", \"" + icfg_name + "\", \"" + inst_name + "\"")
    # Run the initial OCI config routine.
    try:
        cfg = config_setup()
    except: 
        print("\"config_setup\" routine FAILED.")
        sys.exit(ERROR_MSG)
    if VERBOSE:
        print("Configuration/authentication succeeded.")
    
    #Get the ID for our tenancy (also root directory)
    VSI_TENANCY_ID=get_tenancy_ocid()
    # Get the list of compartments from Identity Client
    cmgr=oci.identity.IdentityClient(cfg)
    list_compartments_response = cmgr.list_compartments(
        compartment_id=VSI_TENANCY_ID,
        compartment_id_in_subtree=True)
    # Get the list of compartments including child compartments except root compartment
    compartmentlist = list_compartments_response.data
    # Get the details of root compartment & append to the compartment list so that we have the full list of compartments in the given tenancy
    root_compartment = cmgr.get_compartment(compartment_id=VSI_TENANCY_ID).data
    compartmentlist.append(root_compartment)
    # Go through the compartment list and see if the one specified exists.
    cur_cmpt=None
    for cptm in compartmentlist:
        if(cptm.name == cmpt_name):
            cur_cmpt=cptm
            break      
    if cur_cmpt is None:
        print("Compartment \"" + cmpt_name + "\" not found in tenancy.")
        return
    #CUR_CMPT=cur_cmpt
    print("Compartment is now set to: " + cur_cmpt.name)
    #cmgr=oci.core.ComputeManagementClient(cfg)
    cmc_cmgr=oci.core.ComputeManagementClient(cfg)
    icfgs=cmc_cmgr.list_instance_configurations(cur_cmpt.id).data
    icfg=None
    for ic in icfgs:
        if(icfg_name == ic.display_name):
            icfg=ic
            break
    if icfg is None:
        print("Instance config \"" + icfg_name + "\" not found in compartment " + cur_cmpt.name)
        return
    print("Using Instance configuration \"" + icfg_name + "\"")
    print("Instance name: ", end='')
    if(inst_name == ""):
        print(" UNSPECIFIED (let oci choose name)")
    else:
        print(inst_name)
    if(inst_name != ""):
        launch_det=oci.core.models.InstanceConfigurationLaunchInstanceDetails(
                display_name=inst_name)
    else:
        launch_det=oci.core.models.InstanceConfigurationLaunchInstanceDetails()
    
    launch_instance_configuration_response = cmc_cmgr.launch_instance_configuration(
        instance_configuration_id=icfg.id,
        instance_configuration=oci.core.models.ComputeInstanceDetails(
        instance_type="compute",
        launch_details=launch_det))
    
    print(launch_instance_configuration_response.data)
    if inst_name != "":
        print("Instance \"" + inst_name + "\" has been successfuly launched.")
    else:
        print("Instance \"" + launch_instance_configuration_response.data.display_name + "\" has been successfuly launched.")

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a ArcHydro schema')
    parser.add_argument('-c', '--compartment_name', required=True,help='name of the compartment')
    parser.add_argument('-ic', '--instance_cfg_name', required=True,help='name of the instance configuration')
    parser.add_argument('-in', '--instance_name', help='name of the instance (optional)')
    parser.add_argument('-v', '--verbose', action='store_true')
    main_routine(parser.parse_args())