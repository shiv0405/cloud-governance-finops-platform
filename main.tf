provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "project_artifacts" {
  bucket = "${var.project_name}-artifacts-demo"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "transparent-portfolio-manager"
  }
}

