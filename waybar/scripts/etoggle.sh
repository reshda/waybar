#!/usr/bin/env bash

# if no arguments are passed, show usage
if [ $# -eq 0 ]; then
	echo "Usage: $0 <window>"
	exit 1
fi

window="$1"
is_active=`eww active-windows | grep "$window"`
[ "$is_active" ] && eww close "$window" || eww open "$window"

