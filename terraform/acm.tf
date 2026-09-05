# ==============================================================================
# ACM — Certificado Wildcard *.triage.cloud-ip.cc (us-east-1 obrigatório)
# Validação DNS feita manualmente no ClouDNS (zona autoritativa)
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

# Aguarda a validação do certificado (o CNAME de validação foi adicionado
# manualmente no ClouDNS — ver output acm_validation_cname)
resource "aws_acm_certificate_validation" "triage_wildcard" {
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.triage_wildcard.arn
}
