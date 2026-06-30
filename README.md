# JetRacer Remote Machine

This repository is the remote counterpart to the [jetracer_ros2](https://github.com/escher-bach/jetracer_ros2_port) package. It is designed to run on a host machine (laptop / WSL or Docker) to remotely interface with the JetRacer robot.

It offloads heavy processing from the robot's onboard computer by receiving camera streams and sensor data over the network (via Zenoh and Cyclone DDS), and runs all OpenCV-based vision tasks (face tracking, colour tracking, motion detection, contour extraction, etc.), teleoperation, and RViz visualisations locally.

---

## Installation

There are two supported setups. The **Docker + WSLg** path is recommended for Windows users — it is fully reproducible and GUI-capable out of the box.

---

## Option A — Docker + WSLg (Recommended for Windows)

This runs the entire remote stack inside a Docker container. GUI apps (RViz2, OpenCV windows) render natively on your Windows desktop via **WSLg** — no X server or VNC needed.

### Prerequisites

- Windows 10 21H2+ or Windows 11
- WSL 2 with WSLg (ships by default on supported Windows versions — run `wsl --update` to be sure)
- Docker Desktop with the **WSL 2 backend** enabled, **or** Docker Engine installed directly inside WSL 2

> **Check WSLg is working**: Open WSL 2 and run `xclock`. A clock window should appear on your Windows desktop. If it does, you are good to go.

### Setup

1. **Clone the repository inside WSL 2** (not in a Windows path):

   ```bash
   git clone https://github.com/escher-bach/jetracer_remote_machine.git
   cd jetracer_remote_machine
   ```

2. **Set your robot's IP address** in the `.env` file:

   ```bash
   # Edit .env and set ROBOT_IP to your Jetson Nano's IP
   nano .env
   ```

3. **Build and start the containers:**

   ```bash
   docker compose up --build
   ```

   This builds the `jetracer-remote` image (ROS 2 Humble Desktop + OpenCV + Zenoh) and starts the Zenoh bridge pointed at your robot.

4. **Open a shell into the running container:**

   ```bash
   docker exec -it jetracer_remote bash
   ```

5. **Launch any remote node** (GUI windows open automatically on your desktop):

   ```bash
   ros2 launch jetracer_remote rviz_launch.py
   ```

> **Source volume mount**: The `jetracer_remote` package is mounted live from your host into the container (`./jetracer_remote → /ros2_ws/src/jetracer_remote`), so you can edit Python nodes on Windows/WSL and they reflect immediately — no rebuild needed.

---

## Option B — Bare-metal Ubuntu / WSL 2 (Original setup)

## Installation (Ubuntu / WSL 2)

### WSL 2 Mirrored Networking (Required for WSL users)

By default WSL uses NAT, which prevents the robot from discovering your WSL instance. Enable **Mirrored Networking** first:

1. Open File Explorer and go to your user folder (e.g. `C:\Users\YourUsername`).
2. Create or edit the file `.wslconfig` and add:

   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

3. Restart WSL from PowerShell:

   ```cmd
   wsl --shutdown
   ```

### Clone and Run Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/escher-bach/jetracer_remote_machine.git
   cd jetracer_remote_machine
   ```

2. **Run the automated setup script:**

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   The script installs ROS 2 Humble (if missing), Eclipse Cyclone DDS, the Zenoh bridge, initialises `rosdep`, installs all package dependencies, and builds the workspace. This may take several minutes.

3. **Apply the environment changes:**

   ```bash
   source ~/.bashrc
   ```

   *(Or simply close and reopen your terminal.)*

---

## Usage

### Step 1 — Robot side: start the Docker containers

On the JetRacer Jetson Nano, navigate to the **source folder** (`jetracer_ros2_port`) and bring up the stack:

```bash
# On the Jetson, in the jetracer_ros2_port directory
docker compose up
```

This builds and starts two containers:
- `my_jetracer` — the ROS 2 Humble environment (motors, LiDAR, SLAM, Nav2, camera)
- `my_jetracer_zenoh` — the `zenoh-bridge-ros2dds` that tunnels all topics over TCP

Wait for both containers to report healthy before continuing.

### Step 2 — Robot side: launch SLAM, camera, and navigation

In a new terminal on the Jetson, exec into the running container and start the combined launch:

```bash
docker exec -it my_jetracer bash
ros2 launch jetracer_ros2 camera_slam_nav_launch.py
```

Wait until SLAM Toolbox, Nav2, and the camera node are all reported as active.

### Step 3 — Remote machine: connect to the robot

On your laptop / WSL, connect the local Zenoh instance to the robot's bridge:

```bash
zenoh-bridge-ros2dds -e tcp/<robot-ip>:7447
```

Replace `<robot-ip>` with the actual IP address of the Jetson Nano (e.g. `192.168.0.31`).

### Step 4 — Verify topics are visible

```bash
ros2 topic list
```

You should see all robot topics (`/scan`, `/map`, `/odom`, `/csi_cam_0/image_raw/compressed`, etc.) available on the remote machine.

### Step 5 — Launch navigation visualisation

Open RViz2 to monitor and interact with the navigation stack:

```bash
ros2 launch jetracer_remote rviz_launch.py
```

In RViz2, add the relevant topics (`/map`, `/scan_filtered`, `/odom`, the camera image, etc.) to begin monitoring autonomous navigation.

### Step 6 — Launch vision pipeline alongside navigation

While navigation is running, start the contour / edge-detection node to see vision and navigation simultaneously:

```bash
ros2 launch jetracer_remote contours_launch.py
```

---

## Launch File Reference

### Robot-side launch files (`jetracer_ros2` package)

| Launch file | What it starts |
|---|---|
| `jetracer_launch.py` | `jetracer_node` + EKF + static TF publishers |
| `slam_launch.py` | jetracer_launch + sllidar + laser filter + slam_toolbox |
| `camera_slam_nav_launch.py` | SLAM + camera + Nav2 all-in-one (primary demo launch) |
| `localization_launch.py` | Saved-map navigation: jetracer_launch + sllidar + laser filter + map_server + AMCL + Nav2. Accepts `map:=` argument (default: `maps/my_map.yaml`). |
| `nav_launch.py` | Nav2 full bringup (navigation stack only; no built-in localisation) |
| `csi_camera_launch.py` | `gscam_node` reading frames from the shared memory socket |

### Remote-side launch files (`jetracer_remote` package)

| Launch file | What it starts |
|---|---|
| `rviz_launch.py` | RViz2 with the `jetracer.rviz` configuration |
| `cv_video_launch.py` | Basic OpenCV frame display |
| `face_detect_launch.py` | Haar cascade frontal face detection |
| `deep_face_tracking_launch.py` | DNN-based face tracking |
| `color_tracking_launch.py` | HSV colour-space tracking with blob centroid |
| `object_tracking_launch.py` | OpenCV multi-object tracker |
| `contours_launch.py` | Canny edge detection and contour extraction |
| `motion_detect_launch.py` | Frame-differencing motion detection |
| `pose_launch.py` | OpenCV chessboard pose estimation (`solvePnP`) |
| `calibration_launch.py` | Interactive camera calibration utility |
| `joy_launch.py` | Gamepad (joystick) teleoperation |
