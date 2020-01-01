# -*- coding: utf-8 -*-
"""Darkweb crawler & search engine."""

# version string
__version__ = '0.1.0.dev0'

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
    py_modules=['darc'],
    # scripts
    # ext_modules
    classifiers=[
        'Development Status :: 2 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
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
    license='MIT License',
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
        'requests[socks]',
        'selenium',
        'stem',
    ]
)

try:
    from setuptools import setup

    attrs.update(dict(
        include_package_data=True,
        # libraries
        # headers
        # ext_package
        # include_dirs
        # password
        # fullname
        long_description_content_type='text/markdown',
        python_requires='>=3.8',
        zip_safe=True,
    ))
except ImportError:
    from distutils.core import setup

# set-up script for pip distribution
setup(**attrs)
