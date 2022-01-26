from setuptools import setup, find_packages

exec(open('src/gboml/version.py').read())

setup(
    name='gboml',
    version=__version__,
    description='Package of GBOML',
    entry_points={
        'console_scripts': [
            'gboml = gboml:main',
        ]
    },
    author='Miftari B',
    author_email='bmiftari@uliege.be',
    package_dir={'': 'src'},
    install_requires=[
        'numpy>=1.19.4',
        'ply==3.11',
        'scipy>=1.5.3',
    ],
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
