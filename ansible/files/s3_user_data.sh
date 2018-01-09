#!/bin/bash

export BUCKET="s3://umccr-pcgr/"

sudo apt install -y awscli
sudo mount /dev/xvdb /mnt/work
cd /mnt/work/pcgr
sudo chown -R ubuntu:ubuntu /mnt/work/pcgr-0.5.3
latest_vcf=`aws s3 ls $BUCKET | sort | tail -n 1 | grep -v output |  awk '{print $4}'`
aws s3 cp ${BUCKET}${latest_vcf} .
tabix $latest_vcf
python pcgr.py --input_vcf $latest_vcf . output pcgr_configuration.toml $latest_vcf
aws s3 cp --recursive output ${BUCKET}${latest_vcf}-output
