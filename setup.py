import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'deform',
    ]

setup(name='khufu_deform',
      version='0.1',
      description='Deform bindings for Pyramid',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        ],
      license='BSD',
      author='Rocky Burt',
      author_email='rocky@serverzen.com',
      url='https://github.com/serverzen/khufu_deform',
      keywords='pyramid khufu deform',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      test_suite="khufu_deform.tests",
      entry_points='',
      )
