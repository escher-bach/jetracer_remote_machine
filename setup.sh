#!/bin/bash
set -e

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  JetRacer Remote Machine (WSL/Ubuntu) Setup Script   ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "Please do not run this script as root (no sudo). The script will prompt for sudo when needed."
  exit 1
fi

echo -e "\n${GREEN}[1/7] Updating system packages...${NC}"
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl gnupg2 lsb-release build-essential git python3-pip

echo -e "\n${GREEN}[2/7] Checking ROS 2 Installation...${NC}"
# Default to Humble if no ROS_DISTRO is set in the environment
export ROS_DISTRO=${ROS_DISTRO:-humble}

if ! command -v ros2 &> /dev/null; then
    echo "ROS 2 not found. Installing ROS 2 $ROS_DISTRO (Desktop)..."
    sudo apt-get update && sudo apt-get install software-properties-common -y
    sudo add-apt-repository universe -y
    sudo apt-get update && sudo apt-get install curl -y
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y ros-$ROS_DISTRO-desktop python3-argcomplete python3-colcon-common-extensions python3-rosdep python3-vcstool
else
    echo "ROS 2 ($ROS_DISTRO) is already installed."
fi

# Source ROS 2
source /opt/ros/$ROS_DISTRO/setup.bash

echo -e "\n${GREEN}[3/7] Installing Eclipse Cyclone DDS...${NC}"
sudo apt-get install -y ros-$ROS_DISTRO-rmw-cyclonedds-cpp

echo -e "\n${GREEN}[4/7] Installing Eclipse Zenoh...${NC}"
if ! command -v zenoh-bridge-ros2dds &> /dev/null; then
    sudo mkdir -p /etc/apt/keyrings
    curl -L https://download.eclipse.org/zenoh/debian-repo/zenoh-public-key | sudo gpg --dearmor --yes --output /etc/apt/keyrings/zenoh-public-key.gpg
    echo "deb [signed-by=/etc/apt/keyrings/zenoh-public-key.gpg] https://download.eclipse.org/zenoh/debian-repo/ /" | sudo tee /etc/apt/sources.list.d/zenoh.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y zenoh-bridge-ros2dds
else
    echo "Zenoh is already installed."
fi

echo -e "\n${GREEN}[5/7] Initializing and updating rosdep...${NC}"
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init || true
fi
rosdep update

echo -e "\n${GREEN}[6/7] Setting up JetRacer Workspace...${NC}"
WS_DIR="$HOME/jetracer_ws"
mkdir -p "$WS_DIR/src"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Link the jetracer_remote package into the workspace if it's not already there
if [ ! -L "$WS_DIR/src/jetracer_remote" ] && [ ! -d "$WS_DIR/src/jetracer_remote" ]; then
    if [ -d "$SCRIPT_DIR/jetracer_remote" ]; then
        ln -sfn "$SCRIPT_DIR/jetracer_remote" "$WS_DIR/src/jetracer_remote"
        echo "Symlinked jetracer_remote into $WS_DIR/src/"
    else
        echo "Could not find jetracer_remote directory next to this script!"
        exit 1
    fi
fi

cd "$WS_DIR"
echo "Installing ROS dependencies for the workspace..."
rosdep install --from-paths src --ignore-src -r -y

echo "Building the workspace..."
colcon build --symlink-install

echo -e "\n${GREEN}[7/7] Configuring ~/.bashrc...${NC}"
BASHRC="$HOME/.bashrc"

# Function to add a line to bashrc if it doesn't exist
add_to_bashrc() {
    if ! grep -qF "$1" "$BASHRC"; then
        echo "$1" >> "$BASHRC"
    fi
}

echo "" >> "$BASHRC"
echo "# JetRacer Remote Environment" >> "$BASHRC"
add_to_bashrc "source /opt/ros/$ROS_DISTRO/setup.bash"
add_to_bashrc "source $WS_DIR/install/setup.bash"
add_to_bashrc "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp"

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "To start using the environment, please run:"
echo -e "    ${BLUE}source ~/.bashrc${NC}"
echo -e "Or simply close and reopen your WSL terminal."
echo -e "${BLUE}======================================================${NC}"
