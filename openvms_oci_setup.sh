#!/bin/bash


if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

usage() {
    echo "--Program usage--"
    #echo "..."
}

openvms_oci_setup_dir=/home/opc/openvms_oci_setup
openvms_oci_setup_progress=/home/opc/openvms_oci_setup/progress.txt
scr_name=$0
src_name_noext="${scr_name%.*}"
crc_dir="$openvms_oci_setup_dir/crontab_reboot_cmd.sh"
# -r(em_api_key) ?
set_pwds=0
set_api=0
set_vnd_pwd=0


# iterate through arguments 
for var in "$@"
    do
    if [ $var = "-setpwd" ]; then
        echo "Set passwords for users root and opc."
        set_pwds=1
    elif [ $var = "-setvncpwd" ]; then
        echo "Set vncserver password selected."
        set_vnc_pwd=1
    elif [ $var = "-api" ]; then
        echo "Set API session selected."
        set_api=1
    else
        echo "'$var' is an unrecognized command line argument."
        usage
        exit 1
    fi
done


# add a chron entry to reboot into this script (and then enter the proper breakpoint)
reboot_and_continue() {

    sudo crontab -r

    if [ ! -f "$crc_dir" ]; then
        # save the reboot command to a file so it can be put into (and removed) via crontab entries. 
        ctb_str="(crontab -u root -l 
        echo '@reboot /bin/bash $PWD/$scr_name >> $openvms_oci_setup_dir/$src_name_noext.log 2>> $openvms_oci_setup_dir/$src_name_noext.err' ) | 
        crontab -u root -"
        echo "$ctb_str" > $crc_dir
    fi

    if ! sudo bash $crc_dir ; then
        echo "Uh ohs 1"
        exit 1
    fi

    sudo shutdown -r now

}



do_part_one() {

    # enable the cockpit web ui
    sudo systemctl enable --now cockpit.socket

    if [ $set_pwds -gt 0 ]; then
        echo "Setting password for user 'root'."
        passwd
        echo "Setting password for user 'opc'."
        passwd opc
    fi

    sudo yum update -y
    sudo yum groupinstall "Server with GUI" -y
    echo "--Installing KVM/qemu virtualization components..."
    sudo yum -y install qemu-kvm qemu-img virt-manager libvirt libvirt-client virt-install virt-viewer 
    sudo ln -sf /lib/systemd/system/runlevel5.target /etc/systemd/system/default.target

    reboot_and_continue

}


do_part_two() {

    sudo yum install mesa-libGL -y
    sudo yum install tigervnc-server -y

    ##TODO: get a way for this to happen???
    if [ $set_vnc_pwd -gt 0 ]; then
        echo "Enter a vncserver password now..."
        vncpasswd #(run it as opc user)
    fi
    #vncpasswd #(run it as opc user)
    # set your vnc password

    if [ ! -f "/etc/systemd/system/vncserver@:1.service" ]; then

        sudo cp /lib/systemd/system/vncserver@.service /etc/systemd/system/vncserver@:1.service
        file="/etc/systemd/system/vncserver@:1.service"
        cat $file
        # Define the string to search for
        old_string="%i"
        # Define the replacement string
        new_string=":1"
        # Use sed to replace the string
        sudo sed -i "s/$old_string/$new_string/g" "$file"
        # add opc to vncserver as user :1
        echo ":1=opc" >> /etc/tigervnc/vncserver.users
        # run the commands to enable and start the vncserver@1.service
        sudo systemctl daemon-reload
        sudo systemctl enable --now vncserver@:1.service
        sudo systemctl start vncserver@:1.service
        sudo systemctl status vncserver@:1.service
    else
        echo "vncserver file /etc/systemd/system/vncserver@:1.service exists, must be \
            configured manually..."
    fi

    echo "--Installing oci package..."
    sudo dnf install python36-oci-cli -y
    sudo oci

    if [ $set_api -gt 0 ]; then
        echo "--Setting up API key..."
        oci setup config
    fi
 
    #TODO: disable SELINUX
    #$ sudo vi /etc/selinux/config 
    #set SELINUX=disabled
 
    #reboot_and_continue ???

}

# create the openvms_oci_setup directory and/or progress file if they aren't present.
if [ ! -d "$openvms_oci_setup_dir" ]; then
    echo "Directory $openvms_oci_setup_dir does not exist"
    sudo mkdir /home/opc/openvms_oci_setup
fi

if [ ! -f "$openvms_oci_setup_progress" ]; then
    echo "File $openvms_oci_setup_dir does not exist"
    sudo touch /home/opc/openvms_oci_setup/progress.txt
fi

# check how many times we have entered the file to see where to proceed
n_lines_str="$(wc -l $openvms_oci_setup_progress)"
n_lines=$(echo "$n_lines_str" | cut -d ' ' -f 1)

case $n_lines in

  0)
    #echo "ZERO"
    echo "PART ONE" > $openvms_oci_setup_progress
    do_part_one
    ;;

  1)
    #echo "ONE"
    sudo crontab -r
    echo "PART TWO" >> $openvms_oci_setup_progress
    do_part_two
    ;;

  #3)
    #echo "TRES"
    #do_part_three
    #;;

  *)
    #echo "DEFAULT"
    ;;
esac


# after switch (reboot) cases
echo "after switch (reboot) cases"
sudo crontab -r