from setuptools import setup, find_packages

setup(
    name="integration_layer_interface",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask",
        "requests",
        "python-dotenv",
        "loguru",
        "pyyaml"
    ],
    python_requires=">=3.8",
)