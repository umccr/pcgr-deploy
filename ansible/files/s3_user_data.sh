#!/bin/bash

export BUCKET="s3://umccr-pcgr/"

sudo cp /usr/share/zoneinfo/Australia/Melbourne /etc/localtime
sudo mount /dev/xvdb /mnt/work
cd /mnt/work/pcgr
sudo chown -R ubuntu:ubuntu /mnt/work/pcgr-0.5.3
while pgrep unattended; do sleep 10; done;
sudo apt install -y awscli
latest_vcf=`aws s3 ls $BUCKET | sort | tail -n 1 | grep -v output |  awk '{print $4}'`
aws s3 cp ${BUCKET}${latest_vcf} .
tabix -f $latest_vcf
#XXX: horrible hotfixing ongoing, bear with me for now
wget https://raw.githubusercontent.com/brainstorm/pcgr-deploy/master/ansible/files/pcgr_defaults.toml
rm pcgr.py && wget https://raw.githubusercontent.com/brainstorm/pcgr-deploy/master/ansible/files/pcgr.py && chmod +x pcgr.py
python pcgr.py --input_vcf $latest_vcf . output pcgr_defaults.toml $latest_vcf
aws s3 cp --recursive output ${BUCKET}${latest_vcf}-output
