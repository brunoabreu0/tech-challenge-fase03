# ==============================================================================
# Route 53 — Hosted Zone para triage.cloud-ip.cc
# ==============================================================================
resource "aws_route53_zone" "triage" {
  name = var.base_domain

  tags = {
    Name    = "${var.project_name}-zone"
    Project = var.project_name
  }
}

# ------------------------------------------------------------------------------
# Registros ALIAS — cada subdomínio aponta para sua distribuição CloudFront
# ------------------------------------------------------------------------------
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.triage.zone_id
  name    = "api.${var.base_domain}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.api.domain_name
    zone_id                = aws_cloudfront_distribution.api.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "airflow" {
  zone_id = aws_route53_zone.triage.zone_id
  name    = "airflow.${var.base_domain}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.airflow.domain_name
    zone_id                = aws_cloudfront_distribution.airflow.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "prometheus" {
  zone_id = aws_route53_zone.triage.zone_id
  name    = "prometheus.${var.base_domain}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.prometheus.domain_name
    zone_id                = aws_cloudfront_distribution.prometheus.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "grafana" {
  zone_id = aws_route53_zone.triage.zone_id
  name    = "grafana.${var.base_domain}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.grafana.domain_name
    zone_id                = aws_cloudfront_distribution.grafana.hosted_zone_id
    evaluate_target_health = false
  }
}
