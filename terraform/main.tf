provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "transparent-portfolio-manager"
  }
}

resource "aws_kms_key" "reporting" {
  description             = "KMS key for the infra reporting starter"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags                    = local.common_tags
}

resource "aws_kms_alias" "reporting" {
  name          = "alias/${local.name_prefix}-reporting"
  target_key_id = aws_kms_key.reporting.key_id
}

resource "aws_s3_bucket" "reporting_lake" {
  bucket = "${local.name_prefix}-${data.aws_caller_identity.current.account_id}-lake"
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "reporting_lake" {
  bucket = aws_s3_bucket.reporting_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reporting_lake" {
  bucket = aws_s3_bucket.reporting_lake.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.reporting.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "reporting_lake" {
  bucket                  = aws_s3_bucket.reporting_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "reporting_lake" {
  bucket = aws_s3_bucket.reporting_lake.id

  rule {
    id     = "report-retention"
    status = "Enabled"

    filter {
      prefix = var.report_prefix
    }

    transition {
      days          = 45
      storage_class = "STANDARD_IA"
    }
  }
}

resource "aws_glue_catalog_database" "reporting" {
  name = replace("${local.name_prefix}_reporting", "-", "_")
}

resource "aws_athena_workgroup" "reporting" {
  name = "${local.name_prefix}-wg"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    result_configuration {
      output_location = "s3://${aws_s3_bucket.reporting_lake.bucket}/${var.report_prefix}/athena-results/"
      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = aws_kms_key.reporting.arn
      }
    }
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "reporting_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-report-compiler"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.reporting.arn
  tags              = local.common_tags
}

resource "aws_iam_role" "reporting_lambda" {
  name = "${local.name_prefix}-report-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "reporting_lambda" {
  name = "${local.name_prefix}-report-lambda"
  role = aws_iam_role.reporting_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.reporting_lambda.arn}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.reporting_lake.arn,
          "${aws_s3_bucket.reporting_lake.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.reporting.arn
      }
    ]
  })
}

data "archive_file" "reporting_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/report_handler.py"
  output_path = "${path.module}/.terraform/report_handler.zip"
}

resource "aws_lambda_function" "reporting" {
  function_name = "${local.name_prefix}-report-compiler"
  role          = aws_iam_role.reporting_lambda.arn
  runtime       = "python3.11"
  handler       = "report_handler.lambda_handler"
  filename      = data.archive_file.reporting_lambda.output_path
  source_code_hash = data.archive_file.reporting_lambda.output_base64sha256
  timeout       = 60

  environment {
    variables = {
      REPORT_BUCKET = aws_s3_bucket.reporting_lake.bucket
      REPORT_PREFIX = var.report_prefix
      ATHENA_WORKGROUP = aws_athena_workgroup.reporting.name
      GLUE_DATABASE = aws_glue_catalog_database.reporting.name
    }
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_event_rule" "daily_reporting" {
  name                = "${local.name_prefix}-daily-reporting"
  description         = "Runs the governance reporting Lambda on a schedule"
  schedule_expression = var.schedule_expression
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "daily_reporting" {
  rule      = aws_cloudwatch_event_rule.daily_reporting.name
  target_id = "reporting-lambda"
  arn       = aws_lambda_function.reporting.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.reporting.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_reporting.arn
}
