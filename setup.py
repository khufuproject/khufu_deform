import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'deform',
    'khufu_sqlalchemy',
    'pyramid_jinja2'
    ]

setup(name='khufu_deform',
      version='1.0a1',
      description='Deform bindings and automatic CRUD views for ' \
          'SQLAlchemy models on Pyramid',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        ],
      license='BSD',
      author='Rocky Burt',
      author_email='rocky@serverzen.com',
      url='http://khufuproject.github.com/khufu_deform',
      keywords='pyramid khufu deform',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      test_suite="khufu_deform.tests",
      entry_points='''
      [paste.app_factory]
      demo = khufu_deform.demo:app
      ''',
      )
