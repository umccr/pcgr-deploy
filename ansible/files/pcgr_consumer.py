#!/usr/bin/env python3
# Example usage: ./pcgr_consumer.py pcgr ap-southeast-2 pcgr 10 10 /home/ubuntu

import os
import sys
import gzip
import shutil
import tarfile
import pathlib
import subprocess
import http.client

import boto3
from botocore.exceptions import ClientError

import logging
# Logging boilerplate
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# To console
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

# Daemon arguments
BUCKET=sys.argv[1]
REGION=sys.argv[2]
QUEUE=sys.argv[3]
QUEUE_WAITTIME=int(sys.argv[4]) # in seconds
MAX_RETRIES=int(sys.argv[5])
OUTPUTS=sys.argv[6]

ec2 = boto3.resource('ec2', region_name=REGION)
s3 = boto3.resource('s3', region_name=REGION)
sqs = boto3.resource('sqs', region_name=REGION)


# Create SQS queue if not found
try:
    queue = sqs.get_queue_by_name(QueueName=QUEUE)
except:
    queue = sqs.create_queue(QueueName=QUEUE, Attributes={'DelaySeconds': 5})



def process(sample):
    output_dir = "{}-output".format(sample)

    log.info("Output dir for processing is: {}".format(output_dir))
    os.mkdir(output_dir)

    cmdline = "/mnt/pcgr/pcgr.py --force_overwrite --input_vcf {vcf}.vcf.gz {somatic_flags} /mnt/pcgr {output} {conf}.toml {sample}"

    if "-somatic" in sample:
        cmdline = cmdline.format(vcf=sample,
                                conf=sample,
                                output=output_dir,
                                sample=sample,
                                somatic_flags="--input_cna {}.tsv".format(sample))

        log.info("Processing somatic sample {sample} with commandline {cli}".format(sample=sample, cli=cmdline))

    elif "-germline" in sample:
        cmdline = cmdline.format(vcf=sample,
                                conf=sample,
                                output=output_dir,
                                sample=sample,
                                somatic_flags='')

        log.info("Processing germline sample {sample} with commandline: {cli}".format(sample=sample, cli=cmdline))

    # Format as array for picky subprocess
    str2subpr = cmdline.split(" ")
    str2subpr = list(filter(None, str2subpr)) # Remove empty strings from list
    log.debug("Running PCGR with command line: {cli}".format(cli=str2subpr))

    log.info(subprocess.check_output(str2subpr))


def fetch(sample):
    log.info("Fetching {sample} from s3://{bucket}".format(sample=sample, bucket=BUCKET))
    s3.meta.client.download_file(BUCKET, sample, "{sample}".format(sample=sample))

def untar(sample):
    log.info("Unpacking PCGR input sample {sample}".format(sample=sample))
    with tarfile.open(sample) as tar:
        tar.extractall()

def upload(sample, log_fh):
    log.info("Tarring and uploading PCGR outputs tarball to S3 on bucket s3://{bucket}".format(bucket=BUCKET))

    sample_output = "{sample}-output.tar.gz".format(sample=sample)

    with os.chdir("{out}/{sample}-output".format(OUTPUTS, sample)):
        with tarfile.open(sample_output, "w:gz") as tar:
            outputs = pathlib.Path(OUTPUTS).glob('*')
            for fname in outputs:
                log.info("Tarring up {fname}".format(fname=fname))
                tar.add("{fname}".format(fname=fname))

        # Free up the log handler for next sample
        log.removeHandler(log_fh)
        shutil.copy2("{out}/{sample}.log".format(out=OUTPUTS, sample=sample), 
                     "{out}/{sample}-output".format(out=OUTPUTS, sample=sample))

        s3.meta.client.upload_file(sample_output, BUCKET, sample_output)

def cleanup(sample):
    log.info("Cleaning up for next run (if any)...")
    # Remove output dir and original files
    shutil.rmtree("{}-output".format(sample))
    outputs = pathlib.Path(OUTPUTS).glob('{sample}*.*'.format(sample=sample))
    for fname in outputs:
        os.unlink(fname)
        
    
def teardown(instance):
    """ Kills the instance (worker)
    """
    log.info("Shutting down {instance}".format(instance=instance))

    # Actually terminate it
    ec2.instances.filter(InstanceIds=[instance]).terminate()

#####
## Util functions
def splitext_plus(fname):
    """Split on file extensions, allowing for zipped extensions.
    """
    base, ext = os.path.splitext(fname)
    if ext in [".gz", ".bz2", ".zip"]:
        base, ext2 = os.path.splitext(base)
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
        instance_id = conn.getresponse().read().decode()
    except TimeoutError:
        log.error("You are not inside an EC2 instance? Instance metadata could not be retrieved")
        sys.exit(-1) # For supervisord (or parent process) monitoring this script in the future
    
    return instance_id


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

            # Change to output folder
            os.chdir(OUTPUTS)

            # Log to individual file
            fh = logging.FileHandler("{}.log".format(sample_file))
            fh.setLevel(logging.INFO)
            log.addHandler(fh)
            
            try:
                fetch(sample_file)
                untar(sample_file)

                process(sample_name)
                upload(sample_name, fh)



                cleanup(sample_name)

                # There might be more samples now that we got to process at least one
                retries = MAX_RETRIES
            except ClientError as e:
                print("Unexpected error: {}".format(e))

            log.info("[Main] Sample {sample} processed, deleting from queue".format(sample=sample_file))
            message.delete()


if __name__ == "__main__":
    main()
