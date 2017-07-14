output "public instance name" {
  value = "${aws_instance.pcgr.public_dns}"
}
