provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "project_artifacts" {
  bucket = "${var.project_name}-${var.environment}-artifacts"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "transparent-portfolio-manager"
  }
}

resource "aws_s3_bucket_versioning" "project_artifacts" {
  bucket = aws_s3_bucket.project_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "project_artifacts" {
  bucket = aws_s3_bucket.project_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "project_artifacts" {
  bucket = aws_s3_bucket.project_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
