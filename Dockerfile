FROM osrf/ros:humble-desktop-full-jammy

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install only what osrf/ros:humble-desktop-full-jammy does NOT already provide:
#   - nano, python3-opencv: not in the base image
#   - ros-humble-image-transport-plugins: compressed/theora transports, not in desktop-full
#   - ros-humble-rmw-cyclonedds-cpp, ros-humble-joy, ros-humble-teleop-twist-joy: not in desktop-full
#   - libglu1-mesa, mesa-utils, x11-apps: GL utilities and X11 test tools for WSLg
RUN apt-get update && apt-get install -y \
    nano \
    python3-opencv \
    ros-humble-image-transport-plugins \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-joy \
    ros-humble-teleop-twist-joy \
    libglu1-mesa \
    mesa-utils \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Install Eclipse Zenoh bridge
RUN mkdir -p /etc/apt/keyrings \
    && curl -L https://download.eclipse.org/zenoh/debian-repo/zenoh-public-key \
       | gpg --dearmor --yes --output /etc/apt/keyrings/zenoh-public-key.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/zenoh-public-key.gpg] https://download.eclipse.org/zenoh/debian-repo/ /" \
       > /etc/apt/sources.list.d/zenoh.list \
    && apt-get update \
    && apt-get install -y zenoh-bridge-ros2dds \
    && rm -rf /var/lib/apt/lists/*

# Setup workspace
RUN mkdir -p /ros2_ws/src
WORKDIR /ros2_ws

# Copy package.xml first to cache the slow rosdep install step
COPY jetracer_remote/package.xml src/jetracer_remote/package.xml

# Initialize rosdep and install dependencies
RUN rosdep update \
    && rosdep install -i --from-path src --rosdistro humble -y \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the package source
COPY jetracer_remote src/jetracer_remote

# Build the workspace
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

# Global sourcing for interactive shells
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc \
    && echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc \
    && echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> /root/.bashrc \
    && echo "export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-0}" >> /root/.bashrc

# Copy entrypoint
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
