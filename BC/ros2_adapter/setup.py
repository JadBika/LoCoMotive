from setuptools import setup

package_name = "ros2_adapter"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/vint_nav.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="LoCoMotive Team",
    maintainer_email="team@example.com",
    description="ROS2 adapter nodes for ViNT deployment on LoCoBot",
    license="MIT",
    entry_points={
        "console_scripts": [
            "vint_infer_node = ros2_adapter.vint_infer_node:main",
            "pd_controller_node = ros2_adapter.pd_controller_node:main",
        ],
    },
)
