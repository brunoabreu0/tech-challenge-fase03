terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Descomente para usar S3 como backend remoto (produção)
  # backend "s3" {
  #   bucket = "fiappostech9mletgrupo17-fase03-terraform-state"
  #   key    = "fase03/terraform.tfstate"
  #   region = "sa-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

# Provider adicional em us-east-1 para certificados ACM (obrigatório para CloudFront)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
