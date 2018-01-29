.. _install:

Installation
============

.. _install_prerequisites:

Prerequisites
-------------

* `Python 3.6 <https://python.org>`_, with the following packages (will be installed during the install process, see :ref:`build_and_install_colmto`).:

  * `defusedxml <https://pypi.python.org/pypi/defusedxml>`_
  * `doxypy <https://pypi.python.org/pypi/doxypy>`_
  * `h5py <https://pypi.python.org/pypi/h5py>`_
  * `lxml <https://pypi.python.org/pypi/lxml>`_
  * `matplotlib <https://pypi.python.org/pypi/matplotlib>`_
  * `nose <https://pypi.python.org/pypi/nose>`_
  * `PyYAML <https://pypi.python.org/pypi/PyYAML>`_
  * `sh <https://pypi.python.org/pypi/sh>`_
  * `pygments-style-solarized <https://github.com/shkumagai/pygments-style-solarized>`_ (for building the documentation)

* libhdf5
* libxml
* libyaml
* SUMO (as provided by build instructions for `MacOS <http://sumo.dlr.de/wiki/Installing/MacOS_Build_w_Homebrew>`_,
  `Linux <http://sumo.dlr.de/wiki/Installing/Linux_Build>`_, `Windows <http://sumo.dlr.de/wiki/Installing/Windows_Build>`_.
  Also see `required libraries <http://sumo.dlr.de/wiki/Installing/Linux_Build_Libraries>`_)

Checkout CoLMTO
---------------

.. code-block:: bash

    git clone --recursive https://github.com/SocialCars/colmto.git


Build SUMO Submodule (optional)
-------------------------------

The version of SUMO currently used for my research is referenced as a submodule (hence the ``--recursive`` option above).

Feel free to use any other version, but make sure to set the ``SUMO_HOME`` environment variable correctly.

FreeBSD
^^^^^^^

.. code-block:: bash

    sudo portmaster devel/autoconf textproc/xerces-c3 graphics/proj graphics/gdal x11-toolkits/fox16
    cd colmto/sumo/sumo
    make -f Makefile.cvs
    ./configure --with-xerces=/usr/local --with-proj-gdal=/usr/local
    make -jN

MacOS
^^^^^

.. code-block:: bash

    brew install Caskroom/cask/xquartz autoconf automake gdal proj xerces-c fox
    export CPPFLAGS="$CPPFLAGS -I/opt/X11/include/"
    export LDFLAGS="-L/opt/X11/lib"
    cd colmto/sumo/sumo
    make -f Makefile.cvs
    ./configure --with-xerces=/usr/local --with-proj-gdal=/usr/local
    make -jN

Ubuntu
^^^^^^

.. code-block:: bash

    sudo apt-get install autoconf libproj-dev proj-bin proj-data libtool libgdal-dev libxerces-c-dev libfox-1.6-0 libfox-1.6-dev
    cd colmto/sumo/sumo
    make -f Makefile.cvs
    ./configure
    make -jN

Install Required System Packages
--------------------------------

FreeBSD
^^^^^^^

.. code-block:: bash

    sudo portmaster textproc/libyaml lang/gcc math/openblas math/atlas math/lapack science/hdf5 print/freetype2

MacOS
^^^^^

.. code-block:: bash

    brew install libxml2 homebrew/science/hdf5 libyaml

Ubuntu
^^^^^^

.. code-block:: bash

    sudo apt-get install libyaml-dev libxslt1-dev


.. _build_and_install_colmto:

Build and Install CoLMTO
------------------------

On OSes with include paths other than ``/usr/include``,
e.g., FreeBSD, MacOS export ``CPPFLAGS`` (adjust accordingly):

.. code-block:: bash

    export CPPFLAGS="-I/usr/local/include"

Install dependencies via ``pip3`` (append ``--prefix=`` on MacOS)

.. code-block:: bash

    pip3 install -r requirements.txt --user

Build package

.. code-block:: bash

    python3 setup.py build

Run unit tests

.. code-block:: bash

    python3 setup.py test


Install (local)

.. code-block:: bash

    python3 setup.py install --user

.. _run_colmto:

Run CoLMTO
==========

You can run CoLMTO directly as a script, providing your local python install directory is in your ``$PATH``:
Keep in mind to set ``SUMO_HOME`` accordingly:

.. code-block:: bash

    export SUMO_HOME=~/colmto/sumo/sumo # adjust accordingly
    colmto --runs 1

If you have not installed CoLMTO in the previous section, run it inside the project directory as module.

.. code-block:: bash

    cd colmto
    python3 -m colmto --runs 1

Upon first start CoLMTO creates `YAML <https://en.wikipedia.org/wiki/YAML>`_ formatted default configurations and its log file in ``~/.colmto/``:

.. code-block:: bash

    ~/.colmto/
    ├── colmto.log
    ├── runconfig.yaml
    ├── scenarioconfig.yaml
    └── vtypesconfig.yaml

Further help on command line options can be obtained by running

.. code-block:: bash

    colmto --help