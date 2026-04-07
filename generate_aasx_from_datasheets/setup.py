from setuptools import setup, find_packages

setup(
    name="generate_aasx_from_datasheets",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask",
        "requests",
        "basyx-python-sdk",
    ],
    python_requires=">=3.8",
)