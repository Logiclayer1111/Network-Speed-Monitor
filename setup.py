"""
Setup script for Network Speed Monitor
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="network-speed-monitor",
    version="1.0.0",
    author="Network Speed Monitor Team",
    description="Monitor real network speed bypassing VPN tunnels",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/network-speed-monitor",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "psutil>=5.9.0",
        "wmi>=1.5.1",
        "requests>=2.31.0",
        "speedtest-cli>=2.1.3",
        "apscheduler>=3.10.0",
        "pywin32>=306",
    ],
    entry_points={
        "console_scripts": [
            "speedmon-poller=backend.poller.main:main",
            "speedmon-api=backend.api.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)