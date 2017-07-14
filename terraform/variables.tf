variable "aws_region" {
  description = "The AWS region to create things in."
  default     = "ap-southeast-2"
}

variable "aws_amis" {
  default = {
    "ap-southeast-2" = "ami-ec74648f"
  }
}

variable "key_name" {
  description = "Name of the SSH keypair to use in AWS."
  default = "mba_wwcrc"
}

variable "volsize" {
  description = "How big the EBS volume should be on AWS"
  default = 5
}
