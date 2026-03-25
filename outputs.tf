output "bucket_name" {
  description = "S3 bucket name for project artifacts and report exports"
  value       = aws_s3_bucket.project_artifacts.bucket
}

output "bucket_arn" {
  description = "ARN of the project artifacts bucket"
  value       = aws_s3_bucket.project_artifacts.arn
}

output "aws_region" {
  description = "AWS region used for this deployment"
  value       = var.aws_region
}
