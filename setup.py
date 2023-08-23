import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    requirements = [
        line.strip() for line in f.readlines() if not line.strip().startswith("#")
    ]

setup(
    name="meca4binder",
    version="0.0.1",
    description="MECA bundle providers for BinderHub and repo2docker",
    url="https://github.com/curvenote/meca4binder",
    author="Steve Purves",
    author_email="steve@curvenote.com",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.7",
    extras_require={
        "test": [
            "pytest",
            "pytest-watch",
            "pytest-asyncio",
            "pytest-mock",
            "black",
            "flake8",
            "pytest-cov",
        ]
    },
)
