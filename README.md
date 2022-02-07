Azure_Acquisition_Template
==============================

A template for acquiring  data on an Azure Kinect rig.

# Installation
Instructions for freshly installing an Azure acquisition system on Ubuntu 18 or 20. 


## Install NVIDIA drivers

Check that you have a GPU installed on the device

`sudo lshw -C display`

Installation can be done via GUI in Software & Updates - I used 470 on an NVIDIA GeForce GTX 760)

*reboot if `nvidia-smi` yields an error*

## Install OpenSSL
`sudo apt-get install libssl-dev`

## Install OpenGL
`sudo apt-get install freeglut3-dev`

## Installing Azure-Kinect-Sensor-SDK ([Package Documentation](https://docs.microsoft.com/en-us/windows-server/administration/linux-package-repository-for-microsoft-software) | [GitHub](https://github.com/microsoft/Azure-Kinect-Sensor-SDK/))
**as of 2/4/22 microsoft have not released a binary for Ubuntu 20.04. To install SDK, below we implement a small workaround.**

## install FFMPEG
`sudo apt install ffmpeg`


### UBUNTU 18.04: 
`curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc`

`sudo apt-add-repository https://packages.microsoft.com/ubuntu/20.04/prod`

### UBUNTU 20.04 (workaround, check the github page for the latest): 
`curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo apt-add-repository https://packages.microsoft.com/ubuntu/18.04/prod`

`curl -sSL https://packages.microsoft.com/config/ubuntu/18.04/prod.list | sudo tee /etc/apt/sources.list.d/microsoft-prod.list`

`curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -`



### BOTH: Install libraries
`sudo apt-get update`

`sudo apt install libk4a1.3-dev`

`sudo apt install libk4abt1.0-dev`

`sudo apt install k4a-tools=1.3.0`

### Install Depth Engine
(this should be installed by default as part of libk4a)

### Setup udev rules

`wget https://raw.githubusercontent.com/microsoft/Azure-Kinect-Sensor-SDK/develop/scripts/99-k4a.rules`

`sudo mv 99-k4a.rules /etc/udev/rules.d/`

### Check that the install worked:
First, unplug and re-plug the camera. 

`k4aviewer`

## Install git

`sudo apt-get install git-all`

## Install anaconda
Download the anaconda for linux installer: 
https://www.anaconda.com/products/individual#linux

`bash ~/Downloads/Anaconda[VERSION].sh`


## Create a new conda environment

`conda create -n kinect_acquisition python=3.8`

`conda activate kinect_acquisition`

## Install this package

Navigate to the main direct of this package (the one with `setup.py` in it)

`python setup.py develop`

`pip3 install -r requirements.txt`


## Install jupyter

`conda install jupyter`

**If Jupyter is already installed:** Add this environment as a seperate jupyter kernel 

`conda install -c anaconda ipykernel`
`python -m ipykernel install --user --name=kinect_acquisition`

## start a jupyter notebook

**Optional:** Run notebook in tmux  
`sudo apt install tmux`

``tmux -new acqusitionjupyter`

Start the notebook (either in the tmux session, or not)
`jupyter notebook --no-browser --port=[YOUR PORT] \path\to\repository\`

(tmux session can be quit with `CTRL + b' then 'd')




# Quickstart: acquisition

Acquisition is run through the `start_recording` function, which can be found in the `run_azures` Jupyter notebook.

Briefly, for each camera, a k4a object is created, and a seperate acquisition process running the function `capture_from_azure ` is opened. The function loops continuously over a set duration, sampling depth, ir, and camera data. Synchronization over cameras is handled by a master-subordinate system, offsetting sampling between each camera. 

![Acqusition pipeline](docs/files/Azure-acquisition.png)