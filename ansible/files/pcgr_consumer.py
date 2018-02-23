#!/usr/bin/env python3
# Example usage: ./pcgr_consumer.py pcgr ap-southeast-2 pcgr 10 10

from os import unlink
from os.path import splitext
import sys
import gzip
import shutil
import tarfile
import subprocess
import http.client
from itertools import zip_longest

import boto3
from botocore.exceptions import ClientError


import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Logging boilerplate
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

BUCKET=sys.argv[1]
REGION=sys.argv[2]
QUEUE=sys.argv[3]
QUEUE_WAITTIME=int(sys.argv[4]) # in seconds
MAX_RETRIES=int(sys.argv[5])

ec2 = boto3.resource('ec2', region_name=REGION)
s3 = boto3.resource('s3', region_name=REGION)
sqs = boto3.resource('sqs', region_name=REGION)

# File extensions we care for
exts = [".tsv", ".log", ".tar.gz", ".vcf.gz", ".tbi", ".toml"]

# Create SQS queue if not found
try:
    queue = sqs.get_queue_by_name(QueueName=QUEUE)
except:
    queue = sqs.create_queue(QueueName=QUEUE, Attributes={'DelaySeconds': 5})
    queue = sqs.get_queue_by_name(QueueName=QUEUE)



def process(sample):
    cmdline = "pcgr.py --input_vcf {vcf}.vcf.gz {somatic_flags} . {output_dir}-output {conf}.toml {sample} >& {log}.log"

    if "-somatic" in sample:
        cmdline = cmdline.format(vcf=sample,
                                output_dir=sample,
                                conf=sample,
                                sample=sample,
                                log=sample,
                                somatic_flags="--input_cna {}.tsv".format(sample))

        log.info("Processing somatic sample {sample} with commandline {cli}".format(sample=sample, cli=cmdline))

    elif "-germline" in sample:
        cmdline = cmdline.format(vcf=sample,
                                output_dir=sample,
                                conf=sample,
                                sample=sample,
                                log=sample,
                                somatic_flags='')

        log.info("Processing germline sample {sample} with commandline: {cli}".format(sample=sample, cli=cmdline))

    # Format as array for picky subprocess
    str2subpr = cmdline.split(" ")
    log.debug("Running subprocess.check_call() like so: {cli}".format(cli=str2subpr))

    subprocess.check_output(str2subpr)


def fetch(sample):
    log.info("Fetching {sample} from s3://{bucket}".format(sample=sample, bucket=BUCKET))
    s3.meta.client.download_file(BUCKET, sample, "{sample}".format(sample=sample))

def untar(sample):
    log.info("Unpacking PCGR input sample {sample}".format(sample=sample))
    tar = tarfile.open(sample)
    tar.extractall()
    tar.close()

def upload(sample, bucket):
    log.info("Uploading PCGR outputs tarball to S3 bucket s3://{bucket}".format(bucket=BUCKET))

    sample_output = "{sample}-output.tar.gz".format(sample=sample)

    try:
        tar = tarfile.open(sample_output, "w")
        for name in zip_longest([sample], exts, fillvalue=sample):
            log.info("Tarring up {fname}".format(fname="{}{}".format(name[0], name[1])))
            tar.add("{}{}".format(name[0], name[1]))
        tar.close()
    except FileNotFoundError:
        pass # Just the .tsv not found for germline

    s3.meta.client.upload_file(sample_output, BUCKET, sample_output)
    
def cleanup(sample):
    log.info("Cleaning up for next run (if any)...")
    
    try:
        for ext in exts:
            unlink("{sample}{ext}".format(sample=sample, ext=ext))
        
        # Cleanup output files and tabix indexes too
        unlink("{sample}-output.tar.gz".format(sample=sample))
        unlink("{sample}.vcf.gz.tbi".format(sample=sample))
    except FileNotFoundError:
         pass # Just the .tsv not found for germline or just removed earlier by some other process
        
    
def teardown(instance):
    """ Kills the instance (worker)
    """
    log.info("Shutting down {instance}".format(instance=instance))

    # Actually terminate it
    ec2.terminate_instances(instance)

#####
## Util functions
def splitext_plus(fname):
    """Split on file extensions, allowing for zipped extensions.
    """
    base, ext = splitext(fname)
    if ext in [".gz", ".bz2", ".zip"]:
        base, ext2 = splitext(base)
        ext = ext2 + ext
    return base, ext

def get_instance_id():
    # No Boto3 API method to get an instance-id from within an EC2 instance!?
    # All it would take is wrapping the following, only using python3's stdlib:
    instance_id = None
    log.info("Retrieving instance ID")

    try:
        conn = http.client.HTTPConnection("169.254.169.254", 80)
        conn.request("GET", "/latest/meta-data/instance-id")
        instance_id = conn.getresponse().read()
    except TimeoutError:
        log.error("You are not inside an EC2 instance? Instance metadata could not be retrieved")
        sys.exit(-1) # For supervisord (or parent process) monitoring this script in the future
    
    return instance_id

def compress(fname):
    with open(fname, 'rb') as f_in:
        with gzip.open("{}.gz".format(fname), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def main():
    retries = MAX_RETRIES

    while 1:
        log.info("[Main] Waiting for Queue messages")
        messages = queue.receive_messages(WaitTimeSeconds=QUEUE_WAITTIME)
        
        log.info("[Main] {} retries left".format(retries))
        retries = retries - 1
        if retries <= 0:
            instance_id = get_instance_id()
            teardown(instance_id)

        for message in messages:
            sample_file = message.body
            log.info("[Main] Sample {sample} is ready to process".format(sample=sample_file))
            sample_name = splitext_plus(sample_file)[0] # get rid of .tar.gz extension
            
            try:
                fetch(sample_file)
                untar(sample_file)

                process(sample_name)
                upload(sample_name, BUCKET)
                cleanup(sample_name)

                # There might be more samples now that we got to process at least one
                retries = MAX_RETRIES
            except ClientError as e:
                print("Unexpected error: {}".format(e))


            log.info("[Main] Sample {sample} processed, deleting from queue".format(sample=sample_file))
            message.delete()

if __name__ == "__main__":
    main()