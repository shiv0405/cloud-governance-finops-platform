variable "project_name" {
  type        = string
  description = "Project slug used for naming AWS resources."
  default     = "infra-reporting"
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
  default     = "demo"
}

variable "aws_region" {
  type        = string
  description = "Primary AWS region for the reporting stack."
  default     = "eu-central-1"
}

variable "owner" {
  type        = string
  description = "Owner or platform team responsible for the stack."
  default     = "platform-engineering"
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge schedule for the reporting Lambda."
  default     = "cron(0 6 * * ? *)"
}

variable "report_prefix" {
  type        = string
  description = "S3 prefix for generated reporting artifacts."
  default     = "reports"
}
