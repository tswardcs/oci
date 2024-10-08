

 

import oci
import traceback
import argparse
import sys
from nltk.tokenize import RegexpTokenizer
 

# Global vars
CUR_CMPT=None 
VERBOSE=False
#cfg=None
#exceptions=[]
IDENTITY_CLIENT_INDEX=0
COMPUTE_CLIENT_INDEX=1
COMPUTE_MANAGEMENT_CLIENT_INDEX=2
VCN_INDEX=3
#.. more?
CORE_MGRS=[]

"""
##-get_tenancy_ocid  
#    Get the ocid of our tenancy. (which is also the root directory)
"""
def get_tenancy_ocid():
    return "ocid1.tenancy.oc1..aaaaaaaa7s4zdy3dcyfxojduycq2cu6hsn2bh5l3evrwxp5uknp5e3vkelgq"

"""
##-config_setup  
#    Setup the initial OCI config from the config file and the API private key. 
"""
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


def list_cmd(tokens):
    global CUR_CMPT
    global VERBOSE
    if not (len(tokens) == 2 and tokens[1] == "cmpt"):
        if CUR_CMPT is None:
            print("Current compartment has not been set. (cannot proceed)")
            return
    if(tokens[1] == "vcn" or tokens[1] == "vcns"):   
        vcns=get_core_mgr(VCN_INDEX).list_vcns(CUR_CMPT.id).data
        print("Compartment contains " + str(len(vcns)) + " virtual cloud network", end='')
        if(len(vcns) != 1):
            print("s", end='')
        print(".")
        i = 0
        for vcn in vcns:
            print("VCN[" + str(i) + "]: " + vcn.display_name)
            i+=1
    elif(tokens[1] == "icfg" or tokens[1] == "icfgs"):
        icfgs=get_core_mgr(COMPUTE_MANAGEMENT_CLIENT_INDEX).list_instance_configurations(CUR_CMPT.id).data
        print("Compartment contains " + str(len(icfgs)) + " instance configuration", end='')
        if(len(icfgs) > 1):
            print("s", end='')
        print(".")
        i = 0
        for icfg in icfgs:
            print("ICFG[" + str(i) + "]: " + icfg.display_name)
            i += 1
    elif(tokens[1] == "inst" or tokens[1] == "instances"):
        insts=get_core_mgr(COMPUTE_CLIENT_INDEX).list_instances(CUR_CMPT.id).data
        print("Compartment contains " + str(len(insts)) + " instance", end='')
        if(len(insts) > 1):
            print("s", end='')
        print(".")
        i = 0
        for inst in insts:
            print("INSTANCE[" + str(i) + "]: " + inst.display_name + " : " + inst.lifecycle_state)
            i+=1
    elif tokens[1] == "cmpt" or tokens[1] == "compartment":
        VSI_TENANCY_ID=get_tenancy_ocid()
        cmgr=get_core_mgr(IDENTITY_CLIENT_INDEX)
        list_compartments_response = cmgr.list_compartments(
            compartment_id=VSI_TENANCY_ID,
            compartment_id_in_subtree=True)
        compartmentlist = list_compartments_response.data
        root_compartment = cmgr.get_compartment(compartment_id=VSI_TENANCY_ID).data
        compartmentlist.append(root_compartment)
        i = 0
        for cptm in compartmentlist:
            print("Compartment[" + str(i) + "]: " + cptm.name)
            i+=1
    else:
        print("\"" + tokens[1] + "\" is an invalid LIST subcommand.")
    

def set_cmd(tokens):
    global CUR_CMPT
    global VERBOSE
    ntokens=len(tokens)
    if(tokens[1] == "cmpt" or tokens[1] == "compartment"):
        cname = tokens[2]
        for token in tokens[3:]:
            cname += ' ' + token
        tmp_compartment=get_cmpt(cname)
        if tmp_compartment is None:
            print("Compartment \"" + cname + "\" not found in tenancy.")
            return
        CUR_CMPT=tmp_compartment
        print("Compartment is now set to: " + CUR_CMPT.name)
    else:
        print("\"" + tokens[1] + "\" is an invalid SET subcommand.")


def show_cmd(tokens):
    global CUR_CMPT
    global VERBOSE
    if(len(tokens) == 2 and tokens[1] == "cmpt"):
        list_cmd(['list','cmpt'])
        return
    if CUR_CMPT is None:
        print("Current compartment has not been set. (cannot proceed)")
        return
    ntokens=len(tokens)
    if(tokens[1] == "inst" or tokens[1] == "instance"):
        if(ntokens == 2):
            list_cmd(['list', 'inst'])
        else:
            iname = tokens[2]
            for token in tokens[3:]:
                iname += ' ' + token
            ins=get_instance(iname)
            if ins is None:
                print("Instance \"" + iname + "\" not found in compartment.")
            else:
                print(str(ins))
    elif(tokens[1] == "icfg" or tokens[1] == "instance_config"):
        if(ntokens == 2):
            list_cmd(['list', 'icfg'])
        else:
            icname = tokens[2]
            for token in tokens[3:]:
                icname += ' ' + token
            ic=get_inst_config(icname)
            if ic is None:
                print("Instance Configuration \"" + icname + "\" not found in compartment.")
            else:
                print(str(ic))
    elif(tokens[1] == "vcn"):
        if len(tokens) < 3:
            list_cmd(['list', 'vcn'])
            return
        vcnname = tokens[2]
        for token in tokens[3:]:
            vcnname += ' ' + token
        vcn=get_vcn(vcnname)
        if vcn is None:
            print("VCN \"" + vcnname + "\" not found in compartment.")
            return
        print(str(vcn))
    elif(tokens[1] == "cur"):
        if len(tokens) > 2 and tokens[2]=="cmpt":
            if CUR_CMPT is None:
                print("Current compartment has not yet been set.")
            else:
                print('Current Compartment: ' + str(CUR_CMPT))
        else:
            print("Invalid SHOW command input.")
    elif(tokens[1] == "cmpt"):
        if len(tokens) < 3:
            print("Invalid SHOW CMPT input.")
        else:
            cname=tokens[2]
            for token in tokens[3:]:
                cname += ' ' + token
            tmpcmpt=get_cmpt(cname)
            if tmpcmpt is None:
                print("Compartment \"" + cname + "\" not found in tenancy.")
            else:
                print(str(tmpcmpt))
    else:
        print("\"" + tokens[1] + "\" is an invalid SHOW subcommand.")


def get_vcn(vcn_name):
    global CUR_CMPT
    global VERBOSE
    vcns=get_core_mgr(VCN_INDEX).list_vcns(CUR_CMPT.id).data
    for vcn in vcns:
        if(vcn.display_name == vcn_name):
            return vcn
    return None

def get_instance(inst_name):
    global CUR_CMPT
    global VERBOSE
    insts=get_core_mgr(COMPUTE_CLIENT_INDEX).list_instances(CUR_CMPT.id).data
    for i in insts:
        if(inst_name == i.display_name):
            return i
    return None

def get_core_mgr(cm_index): 
    global CORE_MGRS
    global cfg
    
    # If the core manager has already been generated and stored, return it
    if CORE_MGRS[cm_index] is not None:
        return CORE_MGRS[cm_index]
    # Otherwise generate it, store it and return it
    cmgr=None
    if cm_index == IDENTITY_CLIENT_INDEX:
        cmgr=oci.identity.IdentityClient(cfg)
        CORE_MGRS[cm_index]=cmgr
    elif cm_index == COMPUTE_CLIENT_INDEX:
        cmgr=oci.core.ComputeClient(cfg)
        CORE_MGRS[cm_index]=cmgr
    elif cm_index == COMPUTE_MANAGEMENT_CLIENT_INDEX: 
        cmgr=oci.core.ComputeManagementClient(cfg)
        CORE_MGRS[cm_index]=cmgr
    elif cm_index == VCN_INDEX:
        cmgr=oci.core.VirtualNetworkClient(cfg)
        CORE_MGRS[cm_index]=cmgr
    else:
        print(str(cm_index) + " is outside the valid range of core managers.")
    return cmgr


def get_inst_config(ic_name):
    icfgs=get_core_mgr(COMPUTE_MANAGEMENT_CLIENT_INDEX).list_instance_configurations(CUR_CMPT.id).data
    for ic in icfgs:
        if(ic_name == ic.display_name):
            return ic
    return None


def terminate_cmd(tokens):
    global CUR_CMPT
    global VERBOSE
    ntokens=len(tokens)
    iname=tokens[1]
    if(ntokens > 2):
        for token in tokens[2:]:
            iname += ' ' + token
    inst=get_instance(iname)
    if(inst is None):
        print("Instance \"" + iname + "\" not found in compartment.")
        return
    if(inst.lifecycle_state == "TERMINATED" or
        inst.lifecycle_state == "TERMINATING" or inst.lifecycle_state == "PROVISIONING"):
        print("Instance " + inst.display_name + " state cannot be modified. (in " +
                 inst.lifecycle_state + " state)")
        return
    get_core_mgr(COMPUTE_CLIENT_INDEX).terminate_instance(inst.id)
    print("Instance " + inst.display_name + " successfuly terminated.")

def inst_action(tokens, action):
    global CUR_CMPT
    global VERBOSE
    ntokens=len(tokens)
    iname=tokens[1]
    if(ntokens > 2):
        for token in tokens[2:]:
            iname += ' ' + token
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
                print("Invalid lifecycle state " + inst.lifecycle_state + " of instance " + inst.display_name   + " for request " + i_action)
                return
    get_core_mgr(COMPUTE_CLIENT_INDEX).instance_action(inst.id,i_action)
    print("Sent " + i_action + " command to instance " + inst.display_name)


def launch_cmd(tokens):
    global CUR_CMPT
    global VERBOSE
    icfg_name=""
    inst_name=""
    icfg_name = tokens[1]
    processing_icfg_name = True
    for token in tokens[2:]:
        if(token == "->"):
            processing_icfg_name = False
            continue
        if processing_icfg_name:
            icfg_name += ' ' + token
        else:
            if inst_name == "":
                inst_name = token
            else:
                inst_name += ' ' + token
    icfg=get_inst_config(icfg_name)
    if(icfg is None):
        print("Instance Configuration \"" + icfg_name + "\" not found in compartment.")
        return
    cmgr=get_core_mgr(COMPUTE_MANAGEMENT_CLIENT_INDEX)

    if(inst_name != ""):
        launch_det=oci.core.models.InstanceConfigurationLaunchInstanceDetails(
                display_name=inst_name)
    else:
        launch_det=oci.core.models.InstanceConfigurationLaunchInstanceDetails()
    launch_instance_configuration_response = cmgr.launch_instance_configuration(
        instance_configuration_id=icfg.id,
        instance_configuration=oci.core.models.ComputeInstanceDetails(
        instance_type="compute",
        launch_details=launch_det))
    
    print(launch_instance_configuration_response.data)
    if inst_name != "":
        print("Instance \"" + inst_name + "\" has been successfuly launched.")
    else:
        print("Instance \"" + launch_instance_configuration_response.data.display_name + "\" has been successfuly launched.")


def help_cmd(tokens):
    if len(tokens) == 1:
        print("------Compartment Manager HELP utility---------------")
        print("-HELP")
        print("-EXIT")
        print("-SHOW <INST/ICFG/VCN> [name]")
        print("---\"SHOW INST [name]\" - Show an Insance")
        print("---\"SHOW ICFG [name]\" - Show an Instance Configuration")
        print("---\"SHOW VCN [name]\" - Show a Virtual Cloud Network")
        print("---\"SHOW CUR CMPT\" - Show the current compartment")
        print("-LIST <INST/ICFG/VCN>")
        print("---\"LIST INST\" - List compartment insances")
        print("---\"LIST ICFG\" - List compartment instance configurations")
        print("---\"LIST VCN\" - List comparment Virtual Cloud Networks")
        print("---\"LIST CMPT\" - List comparments within the tenancy (root dir)")
        print("-SET <CMPT>")
        print("---\"SET CMPT <CMPT_NAME>\" - Set the current compartment")
        print("-LAUNCH <icfg_name> ")
        print("---\"LAUNCH <ICFG_NAME> [-> <inst_name>]\" - Launch an instance configuration")
        print("_______Instance commands________")
        print("---START <instance_name>")
        print("---RESET <instance_name>")
        print("---STOP <instance_name>")
        print("---SOFTSTOP <instance_name>")
        print("---TERMINATE <instance_name>")
    else:
        pass
        
def get_cmpt(cmpt_name):
    #Get the ID for our tenancy (also root directory)
    VSI_TENANCY_ID=get_tenancy_ocid()
    # Get the list of compartments from Identity Client
    cmgr=get_core_mgr(IDENTITY_CLIENT_INDEX)
    list_compartments_response = cmgr.list_compartments(
        compartment_id=VSI_TENANCY_ID,
        compartment_id_in_subtree=True)
    # Get the list of compartments including child compartments except root compartment
    compartmentlist = list_compartments_response.data
    # Get the details of root compartment & append to the compartment list so that we have the full list of compartments in the given tenancy
    root_compartment = cmgr.get_compartment(compartment_id=VSI_TENANCY_ID).data
    compartmentlist.append(root_compartment)
    # Go through the compartment list and see if the one specified exists.
    tmp_cmpt=None
    for cptm in compartmentlist:
        if(cptm.name == cmpt_name):
            tmp_cmpt=cptm
            break
    return tmp_cmpt      



def main_routine(args):
    global VERBOSE
    global CUR_CMPT
    global cfg
    
    ERROR_MSG = "Returning ERROR STATUS"
    VERBOSE=args.verbose

    # Run the initial OCI config routine.
    try:
        cfg = config_setup()
    except: 
        print("\"config_setup\" routine FAILED.")
        sys.exit(ERROR_MSG)
    if VERBOSE:
        print("Configuration/authentication succeeded.")
    
    # Set up an (empty) array for the Core Managers.
    for i in range(0, VCN_INDEX+1):
        CORE_MGRS.append(None)
    
    # Check to see if the user provided the compartment name argument.
    if args.compartment_name is not None:
        set_cmd(['set', 'cmpt', args.compartment_name])
        if CUR_CMPT is None:
            sys.exit(ERROR_MSG)
    if VERBOSE:
        if CUR_CMPT is None:
            print("Current compartment is not set. (run LIST/CMPT and SET CMPT <cmpt_name>)")
        else:
            print("Current compartment is: " + CUR_CMPT.name)

    # Enter an input loop to get and parse commands from the user.
    tokenizer = RegexpTokenizer(r'\s+', gaps=True)
    prompt="CPMT_MGR> "
    while True:
        print(prompt, end='')
        line=input()
        tokens = tokenizer.tokenize(line)
        tokens_lr = []
        for token in tokens:
            tokens_lr.append(token.lower())
        if(len(tokens_lr)):
            if(tokens_lr[0] == "exit"):
                if(len(tokens_lr) > 1):
                    print("Invalid EXIT command input")
                else:
                    print("Exiting Compartment Manager, Good Bye.")
                    break
            elif(tokens_lr[0] == "help"):
                help_cmd(tokens_lr)
            elif(tokens_lr[0] == "list"):
                if(len(tokens_lr) < 2):
                    print("Invalid LIST command input.")
                else:
                    list_cmd(tokens_lr)
            elif(tokens_lr[0] == "set"):
                if(len(tokens_lr) < 2):
                    print("Invalid SET command input.")
                else:
                    tokens[1] = tokens[1].lower()
                    set_cmd(tokens)
            elif(tokens_lr[0] == "show"):
                if(len(tokens) < 2):
                    print("Invalid SHOW command input.")
                else:
                    tokens[1] = tokens[1].lower()
                    show_cmd(tokens)           
            elif(tokens_lr[0] == "stop" or 
                (tokens_lr[0] == "soft" or tokens_lr[0] == "softstop") or
                tokens_lr[0] == "start" or tokens_lr[0] == "reset"):
                if CUR_CMPT is None:
                    print("Current compartment is not set. (cannot proceed)")
                else:
                    if(len(tokens_lr) < 2):
                        print("Invalid " + tokens_lr[0] + " command input.")
                    else:
                        inst_action(tokens, tokens_lr[0])
            elif(tokens_lr[0] == "terminate"):
                if CUR_CMPT is None:
                    print("Current compartment is not set. (cannot proceed)")
                else:
                    if(len(tokens_lr) < 2):
                        print("Invalid TERMINATE command input.")
                    else:
                        terminate_cmd(tokens)
            elif(tokens_lr[0] == "launch"):
                if CUR_CMPT is None:
                    print("Current compartment is not set. (cannot proceed)")
                else:
                    if(len(tokens) < 2):
                        print("Invalid LAUNCH command input.")
                    else:
                        launch_cmd(tokens)
            else:
                print('"' + tokens[0] + '" is an invalid command')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a ArcHydro schema')
    parser.add_argument('-c', '--compartment_name', help='the name of the compartment')
    parser.add_argument('-v', '--verbose', action='store_true')
    main_routine(parser.parse_args())

