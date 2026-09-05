output "ec2_instance_id" {
  description = "ID da instância EC2"
  value       = aws_instance.triage_api.id
}

output "ec2_public_ip" {
  description = "IP público da instância EC2"
  value       = aws_instance.triage_api.public_ip
}

# ------------------------------------------------------------------------------
# URLs HTTPS dos serviços (via CloudFront)
# ------------------------------------------------------------------------------
output "api_url" {
  description = "URL da API de inferência (HTTPS via CloudFront)"
  value       = "https://api.${var.base_domain}"
}

output "airflow_url" {
  description = "URL do Airflow Webserver (HTTPS via CloudFront)"
  value       = "https://airflow.${var.base_domain}"
}

output "prometheus_url" {
  description = "URL do Prometheus (HTTPS via CloudFront)"
  value       = "https://prometheus.${var.base_domain}"
}

output "grafana_url" {
  description = "URL do Grafana (HTTPS via CloudFront)"
  value       = "https://grafana.${var.base_domain}"
}

# ------------------------------------------------------------------------------
# Route 53 — nameservers para configurar no ClouDNS
# ------------------------------------------------------------------------------
output "route53_nameservers" {
  description = "Nameservers do Route 53 — adicionar como NS no ClouDNS para 'triage.cloud-ip.cc'"
  value       = aws_route53_zone.triage.name_servers
}
