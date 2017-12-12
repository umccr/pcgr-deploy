#!/bin/bash
apt-get update && apt-get upgrade -y
wget https://github.com/vladsaveliev.keys
cat vladsaveliev.keys >> /home/ubuntu/.ssh/authorized_keys
sudo mount /dev/xvdb /mnt
