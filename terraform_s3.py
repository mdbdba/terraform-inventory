#!/usr/bin/env python

'''
Get Ansible Inventory From Terraform State in S3
=========================================================
This inventory script generates dynamic inventory by reading through
Terraform state files stored in an s3 bucket. Servers and groups are 
defined inside the Terraform state using special resources defined by 
nbering's Terraform Provider for Ansible. Check it out at
https://github.com/nbering/terraform-provider-ansible.

Configuration
=========================================================
This script is using the Python AWS SDK (boto3).  So, it assumes your
aws cli setup is working and uses that.

Environment Variables:
......................

    ANSIBLE_TF_S3_BUCKET
        This will be the name of the s3 bucket to traverse through to
        the inventory from.

'''
import os
import sys
import traceback
import boto3
import json
from terraform import TerraformState
from terraform import TerraformResource
from terraform import AnsibleInventory
from terraform import AnsibleHost
from terraform import AnsibleGroup

default_bucket_name = 'NoBucketDefined'
try:
    bucket_name = os.environ.get('ANSIBLE_TF_S3_BUCKET', default_bucket_name)   
    inventory = AnsibleInventory()
    s3 = boto3.resource('s3')

    if (bucket_name != default_bucket_name and 
        s3.Bucket(bucket_name).creation_date is not None):
        bucket = s3.Bucket(bucket_name)
        files_in_bucket = list(bucket.objects.all())
        state_files = [f.key for f in files_in_bucket]
        for state_file in state_files:
            if os.path.basename(state_file) == 'terraform.tfstate':
                obj = s3.Object(bucket_name, state_file)
                body = json.loads(obj.get()['Body'].read())
                tfstate = TerraformState(body)
                for resource in tfstate.resources():
                    if resource.is_ansible():
                        inventory.add_resource(resource)                    
    
    sys.stdout.write(json.dumps(inventory.to_dict(), indent=2))

except Exception:
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
