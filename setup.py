from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="knetvis",
    version="0.1.0",
    author="Samuel Arogbonlo",
    author_email="sbayo971@gmail.com",
    description="Kubernetes Network Policy Visualization Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/knetvis",
    package_dir={"": "src"},  # Add this line - tells setuptools packages are in src directory
    packages=find_packages(where="src"),  # Update this line - look for packages in src directory
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "kubernetes>=28.1.0",
        "networkx>=3.1",
        "matplotlib>=3.7.1",
        "click>=8.1.3",
        "rich>=13.3.5",
        "pyyaml>=6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "knetvis=knetvis.cli:cli",  
        ],
    },
)