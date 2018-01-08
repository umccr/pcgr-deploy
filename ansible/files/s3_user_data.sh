#!/bin/bash

BUCKET="s3://umccr-pcgr/"

cd /mnt/pcgr
latest_vcf=`aws s3 ls $BUCKET --recursive *.vcf.gz | sort | tail -n 1 | awk '{print $4}’`
python pcgr.py --input_vcf $latest_vcf . output pcgr_configuration.toml $latest_vcf
aws s3 cp —recursive output ${BUCKET}/${latest_vcf}-output
