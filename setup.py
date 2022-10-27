from setuptools import setup

import pathlib


long_description = "\n\n".join([open("README.rst").read()])

install_requires = [
    "Click",
    "GeoAlchemy2>=0.9,!=0.11.*",
    "SQLAlchemy>=1.3",
    "alembic>=1.8",
]

tests_require = [
    "pytest",
    "pytest-asyncio",
    "factory_boy",
    "mock ; python_version<'3.8'",
]

simulation_templates_require = [
    # Note: Change when threedi-api-client has been released
    "threedi-api-client[aio]>=4",
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
    author="Richard Boon",
    author_email="richard.boon@nelen-schuurmans.nl",
    url="https://github.com/nens/threedi-modelchecker",
    license="MIT",
    packages=["threedi_modelchecker"],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        "test": tests_require,
        "simulation_templates": simulation_templates_require,
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "threedi_modelchecker = threedi_modelchecker.scripts:threedi_modelchecker"
        ]
    },
)
