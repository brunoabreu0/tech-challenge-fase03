output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.triage_api.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.triage_api.public_ip
}

output "api_url" {
  description = "API URL (direct EC2)"
  value       = "http://${aws_instance.triage_api.public_ip}:8000"
}

output "grafana_url" {
  description = "Grafana URL (direct EC2)"
  value       = "http://${aws_instance.triage_api.public_ip}:3000"
}
