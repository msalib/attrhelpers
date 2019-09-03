import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="attrhelpers",
    version="0.0.2",
    author="Michael Salib",
    author_email="msalib@gmail.com",
    description="Type based validators for attrs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/msalib/attrhelpers",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    python_requires='>=3.6',
    zip_safe=True,
    keywords=["class", "attribute", "boilerplate"],
    install_requires=["attrs>=17.3.0"],
    extras_require={"tests": ["pytest>=4.0"]},
    include_package_data=True,
    license='Apache 2',
)
