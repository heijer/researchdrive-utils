from setuptools import setup, find_packages
import pathlib

# Read requirements.txt
HERE = pathlib.Path(__file__).parent
with open(HERE / "requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="researchdrive-utils",
    version="1.0.0",
    description="Utilities for interacting with SURF Research Drive API",
    author="Kees den Heijer",
    author_email="kees.denheijer@data2day.nl",
    url="https://github.com/heijer/researchdrive-utils",
    packages=find_packages(where="src"),  # Finds packages in the src/ directory
    package_dir={
        "": "src",
    },
    install_requires=requirements,  # Dependencies from requirements.txt
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "researchdrive_projectfolders=scripts.researchdrive_projectfolders:main",
            "researchdrive_report=scripts.researchdrive_report:main",
            "researchdrive_create_projectfolder=scripts.researchdrive_create_projectfolder:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)
