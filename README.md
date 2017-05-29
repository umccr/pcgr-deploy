Personal Cancer Genome Reporter deployment recipes
==================================================

WARNING: Half baked ansible/kubernetes recipes, use at your own cost/risk.

Quickstart
==========

YMMV, since this assumes that the volume was prepopulated with data on `/mnt/work`:

```
ansible-playbook -i inventory launch_aws.yaml
ssh ubuntu@ec2-54-66-250-119.ap-southeast-2.compute.amazonaws.com
cd /mnt/work/pcgr-0.3.4 && ./run.sh
```

Also the run script does not exist on PCGR, see [an example](https://github.com/sigven/pcgr#step-4-run-example) and adjust it to your inputs.

Deploying PCGR
==============

The following steps assume that you have a previously configured [aws-cli](https://github.com/aws/aws-cli) and have a recent version
of ansible installed (2.3.x). If this is the case, ansible will create 

1. Tweak `ansible/project_vars.yaml` according to your current AWS zones and preferences.
2. `cd ansible && ./create_volume.sh`.
3. Take note of the `volume-id` generated on step 3 and edit `project_vars.yaml` accordingly.
4. Run `ansible-playbook -i inventory launch_aws.yaml` to deploy and install the EC2 instance linked with the previously created volume.
5. SSH into the newly created instance.

If all went well, you should be able to run pcgr [as specified in PCGR README](https://github.com/sigven/pcgr#step-4-run-example).

TODO: Have idempotency with volume creation for better automation (get rid of the `./create_volume.sh` and steps 2,3,4).

Saving money with Spot instances
--------------------------------

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
