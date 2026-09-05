# ==============================================================================
# CloudFront — 4 distribuições HTTPS (uma por serviço)
# Todas usam o mesmo certificado wildcard e o mesmo WAF WebACL
# ==============================================================================

# Local: configurações compartilhadas entre as distribuições
locals {
  cf_origin_id    = "EC2Origin"
  ec2_origin_dns  = aws_instance.triage_api.public_dns
  cert_arn        = aws_acm_certificate_validation.triage_wildcard.certificate_arn
  waf_arn         = aws_wafv2_web_acl.triage.arn

  # Métodos HTTP permitidos para todas as distribuições CloudFront
  # A autorização e perfil read-only são controlados na camada de aplicação (Airflow e Grafana)
  all_methods    = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
  cached_methods = ["GET", "HEAD"]
}

# ------------------------------------------------------------------------------
# 1. API — api.triage.cloud-ip.cc → EC2:8000
# ------------------------------------------------------------------------------
resource "aws_cloudfront_distribution" "api" {
  enabled     = true
  aliases     = ["api.${var.base_domain}"]
  web_acl_id  = local.waf_arn
  price_class = "PriceClass_100"
  comment     = "Medical Triage API — Fase 3"

  origin {
    domain_name = local.ec2_origin_dns
    origin_id   = local.cf_origin_id

    custom_origin_config {
      http_port              = 8000
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = local.cf_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = local.all_methods
    cached_methods         = local.cached_methods
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type", "Accept"]
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = var.allowed_countries
    }
  }

  viewer_certificate {
    acm_certificate_arn      = local.cert_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name    = "${var.project_name}-cf-api"
    Project = var.project_name
  }
}

# ------------------------------------------------------------------------------
# 2. Airflow — airflow.triage.cloud-ip.cc → EC2:8080 (somente-leitura)
# ------------------------------------------------------------------------------
resource "aws_cloudfront_distribution" "airflow" {
  enabled     = true
  aliases     = ["airflow.${var.base_domain}"]
  web_acl_id  = local.waf_arn
  price_class = "PriceClass_100"
  comment     = "Airflow Webserver — Fase 3 (somente leitura)"

  origin {
    domain_name = local.ec2_origin_dns
    origin_id   = local.cf_origin_id

    custom_origin_config {
      http_port              = 8080
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = local.cf_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = local.all_methods
    cached_methods         = local.cached_methods
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies { forward = "all" }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 60
  }

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = var.allowed_countries
    }
  }

  viewer_certificate {
    acm_certificate_arn      = local.cert_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name    = "${var.project_name}-cf-airflow"
    Project = var.project_name
  }
}

# ------------------------------------------------------------------------------
# 3. Prometheus — prometheus.triage.cloud-ip.cc → EC2:9090 (somente-leitura)
# ------------------------------------------------------------------------------
resource "aws_cloudfront_distribution" "prometheus" {
  enabled     = true
  aliases     = ["prometheus.${var.base_domain}"]
  web_acl_id  = local.waf_arn
  price_class = "PriceClass_100"
  comment     = "Prometheus — Fase 3 (somente leitura)"

  origin {
    domain_name = local.ec2_origin_dns
    origin_id   = local.cf_origin_id

    custom_origin_config {
      http_port              = 9090
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = local.cf_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = local.all_methods
    cached_methods         = local.cached_methods
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 30
  }

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = var.allowed_countries
    }
  }

  viewer_certificate {
    acm_certificate_arn      = local.cert_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name    = "${var.project_name}-cf-prometheus"
    Project = var.project_name
  }
}

# ------------------------------------------------------------------------------
# 4. Grafana — grafana.triage.cloud-ip.cc → EC2:3000 (somente-leitura)
# ------------------------------------------------------------------------------
resource "aws_cloudfront_distribution" "grafana" {
  enabled     = true
  aliases     = ["grafana.${var.base_domain}"]
  web_acl_id  = local.waf_arn
  price_class = "PriceClass_100"
  comment     = "Grafana — Fase 3 (somente leitura)"

  origin {
    domain_name = local.ec2_origin_dns
    origin_id   = local.cf_origin_id

    custom_origin_config {
      http_port              = 3000
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = local.cf_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = local.all_methods
    cached_methods         = local.cached_methods
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies { forward = "all" }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 60
  }

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = var.allowed_countries
    }
  }

  viewer_certificate {
    acm_certificate_arn      = local.cert_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name    = "${var.project_name}-cf-grafana"
    Project = var.project_name
  }
}
