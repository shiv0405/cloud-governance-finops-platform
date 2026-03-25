output "reporting_bucket_name" {
  value       = aws_s3_bucket.reporting_lake.bucket
  description = "S3 bucket used for reporting artifacts."
}

output "athena_workgroup_name" {
  value       = aws_athena_workgroup.reporting.name
  description = "Athena workgroup for governance analysis."
}

output "glue_database_name" {
  value       = aws_glue_catalog_database.reporting.name
  description = "Glue catalog database for report datasets."
}

output "lambda_function_name" {
  value       = aws_lambda_function.reporting.function_name
  description = "Scheduled Lambda that orchestrates reporting jobs."
}
