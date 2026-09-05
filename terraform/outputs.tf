output "ec2_instance_id" {
  description = "ID da instância EC2"
  value       = aws_instance.triage_api.id
}

output "ec2_public_ip" {
  description = "IP público da instância EC2"
  value       = aws_instance.triage_api.public_ip
}

# ------------------------------------------------------------------------------
# URLs HTTPS finais (via CloudFront)
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
# Domínios CloudFront — adicionar como CNAME no ClouDNS após o apply
# ------------------------------------------------------------------------------
output "cloudfront_api_domain" {
  description = "Domínio CloudFront da API — criar CNAME api.triage.cloud-ip.cc → este valor"
  value       = aws_cloudfront_distribution.api.domain_name
}

output "cloudfront_airflow_domain" {
  description = "Domínio CloudFront do Airflow — criar CNAME airflow.triage.cloud-ip.cc → este valor"
  value       = aws_cloudfront_distribution.airflow.domain_name
}

output "cloudfront_prometheus_domain" {
  description = "Domínio CloudFront do Prometheus — criar CNAME prometheus.triage.cloud-ip.cc → este valor"
  value       = aws_cloudfront_distribution.prometheus.domain_name
}

output "cloudfront_grafana_domain" {
  description = "Domínio CloudFront do Grafana — criar CNAME grafana.triage.cloud-ip.cc → este valor"
  value       = aws_cloudfront_distribution.grafana.domain_name
}

# ------------------------------------------------------------------------------
# CNAME de validação ACM — já adicionado manualmente no ClouDNS
# ------------------------------------------------------------------------------
output "acm_validation_cname" {
  description = "CNAME de validação do certificado ACM (já adicionado no ClouDNS)"
  value = {
    name  = tolist(aws_acm_certificate.triage_wildcard.domain_validation_options)[0].resource_record_name
    value = tolist(aws_acm_certificate.triage_wildcard.domain_validation_options)[0].resource_record_value
  }
}
