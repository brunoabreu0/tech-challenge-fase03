# ==============================================================================
# WAF — Web ACL compartilhado entre as 4 distribuições CloudFront
# Escopo CLOUDFRONT exige que o recurso fique em us-east-1
# ==============================================================================
resource "aws_wafv2_web_acl" "triage" {
  provider    = aws.us_east_1
  name        = "${var.project_name}-waf"
  description = "Shared WAF: rate limiting and geo-blocking BR-PT for all Fase 3 services"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Regra 1 — Rate limiting: máximo 2000 req / 5 min por IP
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = false
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = false
    }
  }

  # Regra 2 — Geo-bloqueio: apenas Brasil e Portugal
  rule {
    name     = "GeoBlockRule"
    priority = 2

    action {
      block {}
    }

    statement {
      not_statement {
        statement {
          geo_match_statement {
            country_codes = var.allowed_countries
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = false
      metric_name                = "GeoBlockRule"
      sampled_requests_enabled   = false
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = false
    metric_name                = "${var.project_name}-waf"
    sampled_requests_enabled   = false
  }

  tags = {
    Name    = "${var.project_name}-waf"
    Project = var.project_name
  }
}
