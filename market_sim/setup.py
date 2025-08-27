from setuptools import setup, find_packages

setup(
    name="market-sim",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    author="Torbellino Tech SL",
    author_email="juan.diez@torbellino.tech",
    description="Market dynamics and trading simulation framework",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://www.torbellino.tech/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
)