import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

VERSION = "0.0.1"
PACKAGE_NAME = "genna"
AUTHOR = "Mihail Dungarov"
AUTHOR_EMAIL = "deeplearnmd@gmail.com"
URL = "https://github.com/md-experiments/anna"

LICENSE = "Apache License 2.0"
DESCRIPTION = "A simple and flexible python annotation framework"
LONG_DESCRIPTION = (HERE / "README.md").read_text()
LONG_DESC_TYPE = "text/markdown"

INSTALL_REQUIRES = [
    "Flask>=1.1.2",
    "Jinja2>=2.11.3",
    "numpy>=1.20.1",
    "pandas>=1.2.3",
    "PyYAML>=5.4.1",
    "Werkzeug>=1.0.1",
    "click<7.2.0,>=7.1.1"
    "passlib"
    ]
CLASSIFIERS = [
        'Development Status :: 4 - Beta',
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Machine Learning",
    ]
KEYWORDS = [
        "machine learning", "text annotation", "text labelling", "natural language processing", "text", "ai", "ml"
    ]

setup(name=PACKAGE_NAME,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type=LONG_DESC_TYPE,
        author=AUTHOR,
        include_package_data=True,
        license=LICENSE,
        author_email=AUTHOR_EMAIL,
        url=URL,
        install_requires=INSTALL_REQUIRES,
        packages=find_packages(),
        classifiers=CLASSIFIERS,
        keywords=KEYWORDS
        )