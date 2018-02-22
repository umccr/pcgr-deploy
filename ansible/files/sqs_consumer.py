#!/usr/bin/env python3

import sys
import boto3
import pathlib
import tarfile
import subprocess

import logging
log = logging.getLogger(__name__)

BUCKET=sys.argv[1]
REGION=sys.argv[2]
QUEUE=sys.argv[3]

s3 = boto3.resource('s3', region_name=REGION)
sqs = boto3.resource('sqs', region_name=REGION)
queue = sqs.get_queue_by_name(QueueName=QUEUE)

def process(sample_name):
    log.info("Processing somatic sample {sample}".format(sample=sample_name))
    no_ext = sample_name # XXX

    cmdline = ['pcgr.py', '--input_vcf', sample_name, '--input_cna', 
                          no_ext+".tsv", ".", sample_name+"-output", 
                          no_ext+".toml", no_ext, ">&", no_ext+".log"]
                          

    log.info("Processing germline sample {sample}".format(sample=sample_name))
    cmdline = ['pcgr.py', '--input_vcf', sample_name, ".", sample_name+"-output", 
                          no_ext+".toml", no_ext, ">&", no_ext+".log"]

    subprocess.check_output(cmdline)


def fetch(sample_name, dest):
    s3.meta.client.download_file(BUCKET, sample_name, dest)

def untar(sample_name):
    log.info("Unpacking PCGR input sample {sample}".format(sample=sample_name))
    pass

def upload(sample_name, bucket):
    log.info("Uploading PCGR outputs tarball to S3 bucket {bucket}".format(bucket=bucket))
    tar cvfz ${no_ext}-output.tar.gz output_${no_ext} ${no_ext}.toml ${no_ext}.log
    s3.meta.client.upload_file(${no_ext}-output.tar.gz, BUCKET, ${no_ext}-output.tar.gz)
    
def cleanup(sample_name):
    log.info("Cleaning up for next run (if any)...")
    rm *.tsv
    rm *.log *.tar.gz *.vcf.gz *.tbi *.toml
    rm -rf output_${no_ext}
    mkdir -p output

def teardown():
    """ XXX: Kill the instance where this is running if there are no more samples in the queue?
    """
    pass


def main():
    while 1:
    messages = queue.receive_messages(WaitTimeSeconds=10)
    for message in messages:
        print("Message received: {0}".format(message.body))
        
        fetch()
        untar()
        process()
        upload()
        cleanup()

        message.delete()


if __name__ == "__main__":
    main()