# JetRacer Remote Machine

This repository is the remote counterpart to the [jetracer_ros2](https://github.com/TODO/jetracer_ros2) package. It is designed to run on a host machine (like a laptop or WSL environment) to remotely interface with the JetRacer robot.

It offloads heavy processing from the robot's onboard computer by receiving camera streams and sensor data over the network (via Zenoh and Cyclone DDS), and runs all OpenCV-based vision tasks (face tracking, color tracking, motion detection, etc.), teleoperation, and RViz visualizations locally.

## WSL 2 Mirrored Networking (Important!)

If you are running this in Windows Subsystem for Linux (WSL), you **must** enable Mirrored Networking. By default, WSL uses a NAT (Network Address Translation) layer which prevents the robot from discovering or connecting back to your WSL instance. Mirrored networking shares your Windows IP address directly with WSL.

1. Open File Explorer in Windows and navigate to your user folder (e.g., `C:\Users\YourUsername`).
2. Create or edit a file named `.wslconfig`.
3. Add the following lines:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
4. Open PowerShell or Command Prompt and restart WSL:
   ```cmd
   wsl --shutdown
   ```

## Installation (Ubuntu / WSL)

We provide a fully automated, plug-and-play installation script that handles the entire setup process. It will install ROS 2 (if missing), Eclipse Cyclone DDS, Eclipse Zenoh, initialize `rosdep`, install all required package dependencies, and build the workspace.

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd jetracer_remote_machine
   ```

2. **Run the automated setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Apply the environment changes:**
   ```bash
   source ~/.bashrc
   ```
   *(Or simply close and reopen your terminal).*

## Usage

Once installed, your environment will be automatically configured to communicate with the JetRacer using Eclipse Cyclone DDS and Zenoh. You can launch remote nodes such as RViz or teleoperation directly from this workspace.
