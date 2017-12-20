Quickly launch the PCGR AMI
===========================

This assumes you went through `aws configure` and have the access keys and secrets on your account, then:

    pip install awscli && aws configure (unless you have it installed/configured already)
    git clone https://github.com/umccr/pcgr-deploy && cd pcgr-deploy/awscli
    ./awscli_launch.sh

Then navigate to the AWS console or use `aws ec2 describe-instances` to see the public DNS to login into via
`ssh ubuntu@your_newly_created_instance`

Should launch an spot instance with m4.large, if you wish to change that, tweak it on `launch_spec.json`.
