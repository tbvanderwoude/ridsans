from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()


def parse_requirements(filename):
    with open(filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


setup(
    name="ridsans",
    version="0.3.0",
    author="Thom van der Woude",
    author_email="tbvanderwoude@protonmail.com",
    description="A data reduction package for SANS measurements done at the Reactor Institute Delft using Mantid.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tbvanderwoude/ridsans/",
    project_urls={
        "Bug Tracker": "https://github.com/tbvanderwoude/ridsans/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=parse_requirements("requirements.txt"),
    packages=find_packages(include=["ridsans", "ridsans.*"]),
    python_requires=">=3.9",
)
