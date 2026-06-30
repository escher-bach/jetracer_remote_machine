#!/bin/ash
# Convert ROBOT_IPS (comma-separated) into -e tcp/<ip>:7447 flags
# Example: ROBOT_IPS=192.168.0.22,192.168.0.31
#          → zenoh-bridge-ros2dds -e tcp/192.168.0.22:7447 -e tcp/192.168.0.31:7447

set -e

ARGS=""
IFS=","
for ip in $ROBOT_IPS; do
    ARGS="$ARGS -e tcp/$ip:7447"
done
unset IFS

echo " * Starting: /zenoh-bridge-ros2dds$ARGS"
exec /zenoh-bridge-ros2dds $ARGS
