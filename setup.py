import pathlib

from setuptools import setup

long_description = "\n\n".join([open("README.rst").read()])

install_requires = [
    "threedi-schema==0.217.*",
    "Click",
    "GeoAlchemy2>=0.9,!=0.11.*",
    "SQLAlchemy>=1.4",
]

tests_require = [
    "pytest",
    "pytest-cov",
    "pytest-asyncio",
    "factory_boy",
    "mock ; python_version<'3.8'",
]

rasterio_require = [
    "rasterio>=1.3"
]


def get_version():
    # Edited from https://packaging.python.org/guides/single-sourcing-package-version/
    init_path = pathlib.Path(__file__).parent / "threedi_modelchecker/__init__.py"
    for line in init_path.open("r").readlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name="threedi-modelchecker",
    version=get_version(),
    description="Checks validity of a 3Di schematisation",
    long_description=long_description,
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
    ],
    keywords=[],
    author="Nelen & Schuurmans",
    author_email="info@nelen-schuurmans.nl",
    url="https://github.com/nens/threedi-modelchecker",
    license="MIT",
    packages=["threedi_modelchecker"],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        "test": tests_require,
        "rasterio": rasterio_require,
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "threedi_modelchecker = threedi_modelchecker.scripts:cli"
        ]
    },
)
