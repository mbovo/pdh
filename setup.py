import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    requires = f.read().splitlines()

with open("test-requirements.txt", "r") as f:
    test_requires = f.read().splitlines()


with open("version", "r") as f:
    version = f.read()

setuptools.setup(
    name="pdh",
    version=version,
    author="Manuel Bovo",
    author_email="manuel.bovo@gmail.com",
    description="PagerDuty cli for humans",
    long_description=long_description,
    url="",
    package_data={"": ["*.txt"]},
    include_package_data=True,
    install_requires=requires,
    extras_require={
        "test": test_requires,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Linux",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "pdh=pdh.main:main",
        ]
    },
)
