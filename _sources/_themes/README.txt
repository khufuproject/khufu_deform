Khufu Sphinx Theme
==================

This repository contains Khufu themes for Khufu related projects.
To use a theme in your Sphinx documentation, follow this guide:

1. put this directory as _themes into your docs folder.  Alternatively
   you can also use git submodules to check out the contents there
   or symlink this directory as _themes.

2. add this to your conf.py::

    sys.path.append(os.path.abspath(os.path.join('..', '_themes')))
    html_theme_path = ['../_themes']
    html_theme = 'khufu'

The following themes exist:

- **khufu** - the generic Khufu Project documentation theme
