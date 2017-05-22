Personal Cancer Genome Reporter deployment recipes
==================================================

WARNING: Half baked ansible/kubernetes recipes, use at your own cost/risk.

Deploying PCGR
==============

1. Tweak ansible/project_vars.yaml accordingly.
2. `cd ansible && ./create_volume.sh && ansible-playbook -i inventory -vvv launch_aws.yaml`
3. SSH into the newly created instance

Kubernetes
==========

Open ended experiment for now, there are some errors that need attention:

https://twitter.com/braincode/status/865250048480817152
