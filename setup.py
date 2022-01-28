# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from setuptools import setup, find_packages
from pathlib import Path

exec(Path('src/gboml/version.py').read_text())

requirements = Path("requirements.txt").read_text().strip().split("\n")

long_description = Path("README.md").read_text()

setup(
    name='gboml',
    description='GBOML: Graph-Based Optimization Modeling Language',
    long_description=long_description,
    long_description_content_type='text/markdown',
    version=__version__,
    entry_points={
        'console_scripts': [
            'gboml = gboml:main',
        ]
    },
    author='Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst',
    author_email='bmiftari@uliege.be',
    package_dir={'': 'src'},
    install_requires=requirements,
    extras_require={
        'cplex':  ['cplex'],
        'cbc': ['cylp'],
        'xpress': ['xpress'],
        'gurobi': ['gurobipy'],
        'all_solvers': ['cplex', 'cylp', 'xpress', 'gurobipy']
    },
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Compilers',
    ],
    url='https://gitlab.uliege.be/smart_grids/public/gboml',
    include_package_data=True,
    packages=["gboml"],
)
