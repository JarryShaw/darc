# -*- coding: utf-8 -*-
"""``darc`` - Darkweb Crawler Project
========================================

``darc`` is designed as a swiss army knife for darkweb crawling.
It integrates ``requests`` to collect HTTP request and response
information, such as cookies, header fields, etc. It also bundles
``selenium`` to provide a fully rendered web page and screenshot
of such view.

The general process of ``darc`` can be described as following:

There are two types of *workers*:

* ``crawler`` -- runs the ``darc.crawl.crawler`` to provide a
  fresh view of a link and test its connectability

* ``loader`` -- run the ``darc.crawl.loader`` to provide an
  in-depth view of a link and provide more visual information

"""

import sys
import subprocess  # nosec

version_info = sys.version_info[:2]

# version string
__version__ = '0.9.0'

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
        # version compatibility
        'dataclasses; python_version < "3.7"',
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
    },
    setup_requires=[
        #'bpc-walrus; python_version < "3.8"',
        'python-walrus==0.1.5rc1; python_version < "3.8"',
    ],
)

try:
    from setuptools import setup
    from setuptools.command.build_py import build_py

    attrs.update(dict(
        include_package_data=True,  # type: ignore
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

    def run(self):  # type: ignore[no-untyped-def]
        if version_info < (3, 8):
            try:
                subprocess.check_call(  # nosec
                    [sys.executable, '-m', 'walrus', '--no-archive', 'darc']
                )
            except subprocess.CalledProcessError as error:
                print('Failed to perform assignment expression backport compiling.'
                      'Please consider manually install `bpc-walrus` and try again.', file=sys.stderr)
                sys.exit(error.returncode)
        build_py.run(self)


# set-up script for pip distribution
setup(cmdclass={
    'build_py': build,
}, **attrs)
