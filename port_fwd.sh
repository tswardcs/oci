#!/bin/bash

# 
#
#

usage() {
   echo "Program usage:"
   echo " $ bash port_fwd.sh [-h|-help]"
   echo " $ bash port_fwd.sh <GUEST_IP_ADDR> <START|STOP|RESET> [HOST_PORT]"
}

if [ "$#" -eq 0 ] || ([ "$#" -eq 1 ] && ([ $1 = "-h" ] || [ $1 = "-help" ]));  then
   usage
   exit 0
elif [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Invalid program arguments."
    usage
    exit 1
fi

HOST_PORT=1234
if [ "$#" -eq 3 ]; then
   if [[ $3 -lt 1 ]] || [[ $3 -gt 9999 ]]; then
      echo "$3 is an invalid HOST PORT {1,9999}"
      usage
      exit 1
   fi
   HOST_PORT=$3
fi

read A B C D <<<"${1//./ }"
re='^[0-9]+$'

if ! [[ $A =~ $re ]] || ! [[ $B =~ $re ]] || ! [[ $C =~ $re ]] || ! [[ $D =~ $re ]]; then
   echo "$1 is an invalid IP address (1)"
   usage 
   exit 1
elif [[ $A -gt 0xff ]] || [[ $B -gt 0xff ]] || [[ $C -gt 0xff ]] ||[[ $D -gt 0xff ]]; then
   echo "$1 is an invalid IP address (2)"
   usage
   exit 1
fi


if [ $2 != "start" ] && [ $2 != "stop" ] && [ $2 != "reset" ]; then
   echo "\"$2\" is an invalid ACTION parameter."
   usage
   exit 1
fi

GUEST_IP=$1
GUEST_PORT=23
echo "Guest IP='$GUEST_IP'"
echo "Guest port='$GUEST_PORT'"
echo "Guest port='$HOST_PORT'"
exit 1

if [ "${2}" = "stop" ] || [ "${2}" = "reset" ]; then
   if ! /sbin/iptables -D FORWARD -o virbr0 -p tcp -d $GUEST_IP --dport $GUEST_PORT -j ACCEPT; then
      echo "Error with rule STOP (1)"
      exit 1
   fi
   if ! /sbin/iptables -t nat -D PREROUTING -p tcp --dport $HOST_PORT -j DNAT --to $GUEST_IP:$GUEST_PORT; then
      echo "Error with rule STOP (2)"
      exit 1
   fi
   echo "Successfuly removed port forwarding rule. {$HOST_PORT:$GUEST_IP:$GUEST_PORT}"
fi

if [ "${2}" = "start" ] || [ "${2}" = "reset" ]; then
   if ! /sbin/iptables -I FORWARD -o virbr0 -p tcp -d $GUEST_IP --dport $GUEST_PORT -j ACCEPT; then
      echo "Error adding rule {$HOST_PORT:$GUEST_IP:$GUEST_PORT}" 
      exit 1
   fi
   if ! /sbin/iptables -t nat -I PREROUTING -p tcp --dport $HOST_PORT -j DNAT --to $GUEST_IP:$GUEST_PORT; then
      echo "Error adding rule {$HOST_PORT:$GUEST_IP:$GUEST_PORT} (2)" 
      exit 1
   fi
   echo "Successfuly added port forwarding rule. {$HOST_PORT:$GUEST_IP:$GUEST_PORT}"
fi

