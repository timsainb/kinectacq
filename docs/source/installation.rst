Installation
============

Instructions for freshly installing an Azure acquisition system on
Ubuntu 18 or 20.

Install NVIDIA drivers
----------------------

Check that you have a GPU installed on the device


.. code-block:: console

   $ sudo lshw -C display

Installation can be done via GUI in Software & Updates - I used 470 on
an NVIDIA GeForce GTX 760)

*reboot if ``nvidia-smi`` yields an error*

Install OpenSSL
---------------

.. code-block:: console

   $ sudo apt-get install libssl-dev

Install OpenGL
--------------

.. code-block:: console

   $ sudo apt-get install freeglut3-dev


install FFMPEG
--------------

.. code-block:: console

   $ sudo apt install ffmpeg

Installing Azure-Kinect-Sensor-SDK 
----------------------------------

**as of 2/4/22 microsoft have not released a binary for Ubuntu 20.04. To
install SDK, below we implement a small workaround.**



UBUNTU 18.04:
~~~~~~~~~~~~~

.. code-block:: console

   $ curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc

   $ sudo apt-add-repository https://packages.microsoft.com/ubuntu/20.04/prod

UBUNTU 20.04 (workaround, check the github page for the latest):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add - sudo apt-add-repository https://packages.microsoft.com/ubuntu/18.04/prod
   $ curl -sSL https://packages.microsoft.com/config/ubuntu/18.04/prod.list | sudo tee /etc/apt/sources.list.d/microsoft-prod.list
   $ curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -

BOTH: Install libraries
~~~~~~~~~~~~~~~~~~~~~~~
Note: The k4a versions listed are the ones I used to install on Ubuntu 20.04. You can probably install the newest libraries without issue. 

.. code-block:: console

   $ sudo apt-get update
   $ sudo apt install libk4a1.3-dev
   $ sudo apt install libk4abt1.0-dev
   $ sudo apt install k4a-tools=1.3.0

Install Depth Engine
~~~~~~~~~~~~~~~~~~~~

(this should be installed by default as part of libk4a)

Setup udev rules
~~~~~~~~~~~~~~~~

.. code-block:: console

   $ wget https://raw.githubusercontent.com/microsoft/Azure-Kinect-Sensor-SDK/develop/scripts/99-k4a.rules``
   $ sudo mv 99-k4a.rules /etc/udev/rules.d/

Check that the install worked:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, unplug and re-plug the camera.

.. code-block:: console

   $ k4aviewer

Install git
-----------

.. code-block:: console

   $ sudo apt-get install git-all

Install anaconda
----------------

Download the anaconda for linux installer:
https://www.anaconda.com/products/individual#linux

.. code-block:: console

   $ bash ~/Downloads/Anaconda[VERSION].sh

Create a new conda environment
------------------------------

.. code-block:: console

   $ conda create -n kinect_acquisition python=3.8
   $ conda activate kinect_acquisition

Install this package
--------------------

Download the package (first, navigate to the directory you want to install in): 

.. code-block:: console

   (kinect_acquisition)$ git clone https://github.com/timsainb/kinectacq.git

Navigate to the main directory of this package (the one with ``setup.py``
in it)

.. code-block:: console

   (kinect_acquisition)$ python setup.py develop
   (kinect_acquisition)$ pip3 install -r requirements.txt

Install pyk4a
-------------

.. code-block:: console

   (kinect_acquisition)$ pip3 install pyk4a

Install jupyter
---------------

.. code-block:: console

   (kinect_acquisition)$ conda install jupyter

**If Jupyter is already installed:** Add this environment as a seperate
jupyter kernel

.. code-block:: console

   (kinect_acquisition)$ conda install -c anaconda ipykernel
   (kinect_acquisition)$ python -m ipykernel install --user --name=kinect_acquisition

start a jupyter notebook
------------------------

**Optional:** Run notebook in tmux. 
Tmux allows you to leave the notebook running in the background (like ``screen`` or ``nohup``). With tmux, you can close and reenter your jupyter session at will. 

.. code-block:: console

   (kinect_acquisition)$ sudo apt install tmux
   (kinect_acquisition)$ tmux -new acqusitionjupyter

Start the notebook (either in the tmux session, or not). Switch the port number (8888) with the port of your choosing. 

.. code-block:: console

   (kinect_acquisition)$ jupyter notebook --no-browser --port=8888 /path/to/repository/

(tmux session can be quit with 'CTRL + b' then 'd')


