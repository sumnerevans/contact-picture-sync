import codecs
import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Find the version
with codecs.open(os.path.join(here, 'cps/__init__.py'), encoding='utf-8') as f:
    for line in f:
        if line.startswith('__version__'):
            version = eval(line.split()[-1])
            break

setup(
    name='contact-picture-sync',
    version=version,
    url='https://gitlab.com/sumner/contact-picture-sync',
    description='Download contact pictures from a lot of different sources.',
    long_description=long_description,
    author='Sumner Evans',
    author_email='inquiries@sumnerevans.com',
    license='GPL3',
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: End Users/Desktop',
        'Operating System :: POSIX',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.8',
    ],
    keywords='facebook google github gitlab',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'mechanicalsoup',
        'pillow',
        'requests',
        'selenium',
        'vobject',
    ],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and
    # allow pip to create the appropriate form of executable for the target
    # platform.
    entry_points={
        'console_scripts': [
            'contact-picture-sync=cps.__main__:main',
        ],
    },
)
