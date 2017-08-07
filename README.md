Personal Cancer Genome Reporter deployment recipes
==================================================

WARNING: Half baked ansible/kubernetes recipes, use at your own cost/risk.

Quickstart
==========

YMMV, since this assumes that the volume was prepopulated with data on `/mnt/work`:

```
conda install -c conda-forge ansible>=2.3
ansible-playbook -i inventory launch_aws.yaml
ssh ubuntu@<your_instance>
cd /mnt/work/pcgr-* && time ./pcgr.py --input_vcf cov50-ensemble-annotated-decomposed.vcf.gz --input_cna_segments examples/tumor_sample.COAD.cna.tsv /mnt/work/pcgr-* output UMCCR
```

Deploying PCGR
==============

The following steps assume that you have a previously configured [aws-cli](https://github.com/aws/aws-cli) and have a recent version
of ansible installed (2.3.x):

1. Tweak `ansible/group_vars/vars` according to your current AWS zones and preferences.
2. Run `ansible-playbook -i inventory launch_aws.yaml`.
3. SSH into the newly created instance.

If all went well, you should be able to run pcgr [as specified in PCGR README](https://github.com/sigven/pcgr#step-4-run-example).

(Optional) saving money with Spot instances
-------------------------------------------

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
