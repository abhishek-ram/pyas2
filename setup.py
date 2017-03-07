import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='pyAS2',
    version='0.3.2',
    packages=['pyas2'],
    include_package_data=True,
    license='GNU GPL v2.0',  # example license
    description='A pythonic AS2 application for file tranfers.',
    long_description=README,
    url='http://pyas2.readthedocs.org/en/latest/',
    download_url='https://github.com/abhishek-ram/pyas2/archive/master.zip',
    author='Abhishek Ram',
    author_email='abhishek8816@gmail.com',
    classifiers=[
        #'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
    ],
    keywords='AS2 AS2Server RFC4130 FileTransfer',
    install_requires=[
        'django>1.9, <=1.10.6',
        'cherrypy>6, <=8.9.1',
        'requests',
        'm2crypto',
        'pyasn1'
    ],
)
