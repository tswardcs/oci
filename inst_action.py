
import argparse
import oci
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

def get_instance(inst_name):
    insts=cmgr=oci.core.ComputeClient(cfg).list_instances(CUR_CMPT.id).data
    for i in insts:
        if(inst_name == i.display_name):
            return i
    return None

def terminate_cmd(iname):
    inst=get_instance(iname)
    if(inst is None):
        print("Instance \"" + iname + "\" not found in compartment.")
        return
    if(inst.lifecycle_state == "TERMINATED" or
        inst.lifecycle_state == "TERMINATING" or inst.lifecycle_state == "PROVISIONING"):
        print("Instance " + inst.display_name + " state cannot be modified. (in " +
                 inst.lifecycle_state + " state)")
        return
    cmgr=oci.core.ComputeClient(cfg).terminate_instance(inst.id)
    print("Instance " + inst.display_name + " successfuly terminated.")


def inst_action(iname, action):
    inst=get_instance(iname)
    if(inst is None):
        print("Instance \"" + iname + "\" not found in compartment.")
        return
    if(inst.lifecycle_state == "TERMINATED" or
        inst.lifecycle_state == "TERMINATING" or inst.lifecycle_state == "PROVISIONING"):
        print("Instance " + inst.display_name + " state cannot be modified. (in " +
                 inst.lifecycle_state + " state)")
        return
    if(action == "soft" or action == "softstop"):
        i_action='SOFTSTOP'
    elif(action == "stop"):
        i_action='STOP'
    elif(action == "reset"):
        i_action='RESET'
    elif(action == "start"):
        i_action='START'
    else:
        print("\"" + action + "\" is an invalid instance action.")
        return
    # Check to see if the request makes sense given the current lifecycle state of the instance.
    if(i_action == "SOFTSTOP" or i_action == "STOP" or i_action == "RESET"):
        if(inst.lifecycle_state != "RUNNING"):
            print("Invalid lifecycle state " + inst.lifecycle_state + " of instance " + inst.display_name + "   for request " + i_action)
            return
    elif(i_action == "START"):
        if(inst.lifecycle_state != "STOPPED"):
            print("Invalid lifecycle state " + inst.lifecycle_state + " of instance " + inst.   display_name   + " for request " + i_action)
            return
    cmgr=oci.core.ComputeClient(cfg).instance_action(inst.id,i_action)
    print("Sent " + i_action + " command to instance " + inst.display_name)


def main_routine(args):
    global cfg
    global CUR_CMPT
    VERBOSE=args.verbose
    ERROR_MSG = "Returning ERROR STATUS"
    cmpt_name=args.compartment_name
    inst_name=args.instance_name
    action=args.action.lower()
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
    CUR_CMPT=cur_cmpt
    print("Compartment is now set to: " + cur_cmpt.name)
    if(action == "terminate"):
        terminate_cmd(inst_name)
    elif(action == "start" or action == "stop" or 
         (action == "soft" or action == "softstop") or action == "reset"):
        inst_action(inst_name, action)
    else:
        print("\"" + args.action + "\" is an invalid action command.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a ArcHydro schema')
    parser.add_argument('-c', '--compartment_name', required=True,help='name of the compartment')
    parser.add_argument('-i', '--instance_name', required=True,help='name of the instance')
    parser.add_argument('-a', '--action', required=True,help='name of the action')
    parser.add_argument('-v', '--verbose', action='store_true')
    main_routine(parser.parse_args())