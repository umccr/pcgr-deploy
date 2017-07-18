provider "aws" {
  region     = "ap-southeast-2"
}

resource "aws_instance" "pcgr" {
  ami           = "ami-ec74648f"
  instance_type = "t2.micro"
  security_groups = ["default"]
  key_name = "mba_wwcrc"
  
  provisioner "local-exec" {
    command = "ansible-playbook ../ansible/site.yml -T 60 -e 'ansible_python_interpreter=/usr/bin/python3' -i ${aws_instance.pcgr.public_dns},"
  }
}

resource "aws_ebs_volume" "pcgr_volume"  {
      availability_zone = "${aws_instance.pcgr.availability_zone}"
      type = "gp2"
      size = "${var.volsize}"
} 

resource "aws_volume_attachment" "pcgr_volume_attach" {
  device_name = "/dev/xvdf"
  instance_id = "${aws_instance.pcgr.id}"
  volume_id   = "${aws_ebs_volume.pcgr_volume.id}"
}