============
khufu_deform
============

Overview
========

*khufu_deform* is a framework component providing integration between
the deform form library, SQLAlchemy, and the Pyramid web application platform.

On a higher level, *khufu_deform* can be used to provide automatic CRUD
views for SQLAlchemy models.

Requirements
============

  * Python >= 2.5 (not tested with Python 3.x series)

Setup
=====

Simply include the ``khufu_deform`` package with the configurator, ie:

.. code-block:: python
 :linenos:

 config.include('khufu_deform')

Usage
=====

The standard way to setup CRUD views is as follows:

.. code-block:: python
 :linenos:

 # config is an instance of Configurator
 # Note is a SQLAlchemy-based model class
 # NoteContainer is the traversal parent containing Notes

 config.include('khufu_deform')
 config.add_crud_views(Note, NoteContainer)

For a more complete example please see the ``khufu_deform.demo`` python module.

Configurator Directives
=======================

Including *khufu_deform* with a ``Configurator`` instance makes available
the following directives:

  - ``add_crud_views`` - Maps default crud views against a given model class

  - ``add_add_form_view`` - Map a view containing a form for adding new instances
 
  - ``add_edit_form_view`` - Map a view containing a form for editing instances
 
  - ``add_list_view`` - Map a view for listing instances of the model
 
  - ``add_view_view`` - Map a view for displaying an instance
 
See :ref:`khufu_deform_api` for more information.


Credits
=======

  * Developed and maintained by Rocky Burt <rocky AT serverzen DOT com>

More Information
================

.. toctree::
 :maxdepth: 1

 api.rst
 glossary.rst

Indices and tables
==================

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
