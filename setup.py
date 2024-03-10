from setuptools import setup

setup(
    name="masscode-driver",
    version="1.0.1",
    description="Driver for MassCode",
    author="ZackaryW",
    url="https://github.com/ZackaryW/masscode-driver",
    packages=[
        "masscodeDriver",
    ],
    install_requires=[
        "thefuzz",
    ],
    python_requires=">=3.8",
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        # audience
        "Intended Audience :: Developers",
    ]
)