Quickly launch the PCGR AMI
===========================

This assumes you went through `aws configure` and have the access keys and secrets on your account, then:

    ./awscli_launch.sh

Should launch an spot instance with m4.large, if you wish to change that, tweak it on `launch_spec.json`.
