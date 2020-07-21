# -*- coding: utf-8 -*-
"""Darkweb crawler & search engine."""

import sys
import subprocess

# version string
__version__ = '0.6.4'

# setup attributes
attrs = dict(
    name='python-darc',
    version=__version__,
    description='Darkweb crawler & search engine.',
    long_description=__doc__,
    author='Jarry Shaw',
    author_email='jarryshaw@icloud.com',
    maintainer='Jarry Shaw',
    maintainer_email='jarryshaw@icloud.com',
    url='https://github.com/JarryShaw/darc',
    download_url='https://github.com/JarryShaw/darc/archive/v%s.tar.gz' % __version__,
    # py_modules
    packages=[
        'darc',
        'darc.proxy',
        'darc.sites'
    ],
    # scripts
    # ext_modules
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development',
        'Topic :: Utilities',
        'Typing :: Typed',
    ],
    # distclass
    # script_name
    # script_args
    # options
    license='BSD 3-Clause License',
    keywords=[
        'darkweb',
        'crawler',
    ],
    platforms=[
        'any'
    ],
    # cmdclass
    # data_files
    # package_dir
    # obsoletes
    # provides
    # requires
    # command_packages
    # command_options
    package_data={
        '': [
            'LICENSE',
            'README.md',
        ],
    },
    # include_package_data
    # libraries
    # headers
    # ext_package
    # include_dirs
    # password
    # fullname
    # long_description_content_type
    # python_requires
    # zip_safe,
    install_requires=[
        'beautifulsoup4[html5lib]',
        'file-magic',
        'peewee',
        'python-datauri',
        'redis[hiredis]',
        'requests-futures',
        'requests[socks]',
        'selenium',
        'stem',
        'typing_extensions',
    ],
    entry_points={
        'console_scripts': [
            'darc = darc.__main__:main',
        ]
    },
    extras_require={
        # database
        'SQLite': ['pysqlite3'],
        'MySQL': ['PyMySQL[rsa]'],
        'PostgreSQL': ['psycopg2'],
        # version compatibility
        ':python_version < "3.8"': ['python-walrus'],
        ':python_version < "3.7"': ['dataclasses'],
    },
)

try:
    from setuptools import setup
    from setuptools.command.build_py import build_py

    version_info = sys.version_info[:2]

    attrs.update(dict(
        include_package_data=True,
        # libraries
        # headers
        # ext_package
        # include_dirs
        # password
        # fullname
        long_description_content_type='text/x-rst',
        python_requires='>=3.6',
        # zip_safe=True,
    ))
except ImportError:
    from distutils.core import setup
    from distutils.command.build_py import build_py


class build(build_py):
    """Add on-build backport code conversion."""

    def run(self):
        if version_info < (3, 8):
            subprocess.check_call(
                ['walrus', '--no-archive', 'darc']
            )
        build_py.run(self)


# set-up script for pip distribution
setup(cmdclass={
    'build_py': build,
}, **attrs)
