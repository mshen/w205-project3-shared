
#!/bin/bash

sudo apt update
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt update  
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8

update-alternatives --install /usr/bin/python python /usr/bin/python3.8 15

sudo apt-get install python3.8-distutils
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py --force-reinstall

python -m  pip install flask
python -m pip install http.client
python -m pip install numpy
python -m pip install requests
python -m pip install kafka-python


#install apache bench
apt-get update
apt-get install apache2-utils
