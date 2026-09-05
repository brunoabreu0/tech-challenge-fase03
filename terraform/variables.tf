variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "sa-east-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "medical-triage-fase03"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "dockerhub_image" {
  description = "Docker Hub image for the triage API"
  type        = string
  default     = "techchallengefase03/medical-triage-api:latest"
}

variable "allowed_countries" {
  description = "Countries allowed through CloudFront WAF geo-restriction"
  type        = list(string)
  default     = ["BR", "PT"]
}
