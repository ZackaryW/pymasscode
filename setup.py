from setuptools import setup

setup(
    name="pymasscode",
    version="1.0.0b1",
    description="Masscode query and api wrapper",
    author="ZackaryW",
    url="https://github.com/ZackaryW/masscode-driver",
    packages=[
        "pymasscode",
        "pymasscode.etc",
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