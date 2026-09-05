# ==============================================================================
# ACM — Certificado Wildcard *.triage.cloud-ip.cc (us-east-1 obrigatório)
# ==============================================================================
resource "aws_acm_certificate" "triage_wildcard" {
  provider          = aws.us_east_1
  domain_name       = "*.triage.cloud-ip.cc"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name    = "${var.project_name}-wildcard-cert"
    Project = var.project_name
  }
}

# Registros DNS de validação no Route 53 (automático via Terraform)
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.triage_wildcard.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = aws_route53_zone.triage.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60

  allow_overwrite = true
}

# Aguarda a validação do certificado antes de criar as distribuições
resource "aws_acm_certificate_validation" "triage_wildcard" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.triage_wildcard.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
