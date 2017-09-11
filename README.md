Personal Cancer Genome Reporter deployment recipes
==================================================

Introduction
============

Cancer reporting systems require prepopulating several gigabytes of genomic reference data and provisioning all software pieces, docker containers and configuration.

PCGR eases that, `pcgr-deploy` simplifies it futher.

This ansible playbook contains tasks to deploy [PCGR](https://github.com/sigven/pcgr) into Amazon and OpenStack clouds, with HPC-specific tasks added as a module (mainly NFS mounting).

Quickstart
==========

Tweak files `ansible/group_vars/all` and `ansible.site.yml`'s roles section according to your needs (are you a HPC or AWS user?).

The following lines will install the deployment modules, deploy PCGR and run its built-in example as a validation:

```
conda install -c conda-forge ansible>=2.3
ansible-playbook aws.yaml
ssh ubuntu@<AWS INSTANCE>
cd /mnt/work/pcgr-*
./pcgr.py --input_vcf examples/tumor_sample.COAD.vcf.gz --input_cna examples/tumor_sample.COAD.cna.tsv /mnt/work/pcgr-* output tumor_sample.COAD
```

Amazon or OpenStack or HPC?
===========================

This playbook allows for all of them, it has tested on the [Australian NCI supercomputing centre Tenjin private cloud](https://nci.org.au/systems-services/cloud-computing/tenjin/).

The only changes needed are on `ansible/group_vars/all` as mentioned on the Quickstart and rearranging `site.yml` so that it includes the `hpc` role after `common` and `databundle`.Then running the playbook in the following way should deploy PCGR in your (OpenStack?) VM:

```
ansible-playbook site.yml -e 'ansible_python_interpreter=/usr/bin/python3' -i <YOUR CLUSTER IP/HOSTNAME>,
```

(Optional) Amazon: Saving money with Spot instances
---------------------------------------------------

The following script included in `ansible` queries AWS's spot history and determines if the
instance we are asking for will be available. For instance, running the script with a `0.08AUD`
asking price gives us:

```
python ~/bin/get_spot_duration.py \
	--region ap-southeast-2 \
	--product-description 'Linux/UNIX' \
	--bids c4.large:0.08
```

That is 168 hours uptime at that particular asking price for `ap-southeast-2c`, that 
is ~87% savings at the time of writing this:

```
$ ./get_spot_duration.sh
Duration    Instance Type    Availability Zone
168.0    c4.large    ap-southeast-2c
108.2    c4.large    ap-southeast-2a
15.7    c4.large    ap-southeast-2b
```

Kubernetes
==========

Open ended experiment for now, there are some errors that [need some attention](https://twitter.com/braincode/status/865250048480817152).

FAQ
===

`ERROR: package is not a legal parameter in an Ansible task or handler` is a symptom of a too old ansible version (probably 1.9.x). You need 2.x to deploy this.
