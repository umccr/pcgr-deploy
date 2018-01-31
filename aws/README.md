Amazon Web Services for PCGR
============================

Quickly launch the PCGR AMI via AWSCLI
======================================

This assumes you went through `aws configure` and have the access keys and secrets on your account, then:

    pip install awscli && aws configure (unless you have it installed/configured already)
    git clone https://github.com/umccr/pcgr-deploy && cd pcgr-deploy/aws/cli
    ./awscli_launch.sh

Then navigate to the AWS console or use `aws ec2 describe-instances` to see the public DNS to login into via
`ssh ubuntu@your_newly_created_instance`


Lambda event S3 code
====================

If you want to just drop your VCF file into a S3 bucket and trigger a StackStorm workflow out of it, this
.yaml and .py code is for you.
