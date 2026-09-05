variable "aws_region" {
  description = "Região AWS para todos os recursos"
  type        = string
  default     = "sa-east-1"
}

variable "project_name" {
  description = "Prefixo de nome para todos os recursos"
  type        = string
  default     = "medical-triage-fase03"
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  type        = string
  default     = "t3.small"
}

variable "dockerhub_image" {
  description = "Imagem Docker Hub da API de triagem"
  type        = string
  default     = "techchallengefase03/medical-triage-api:latest"
}

variable "allowed_countries" {
  description = "Países permitidos pelo geo-bloqueio do WAF/CloudFront"
  type        = list(string)
  default     = ["BR", "PT"]
}

variable "base_domain" {
  description = "Domínio base gerenciado pela hosted zone do Route 53"
  type        = string
  default     = "triage.cloud-ip.cc"
}
