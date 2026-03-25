variable "project_name" {
  description = "Portfolio project name used for tagging and naming."
  type        = string
  default     = "infra-reporting-starter"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "demo"
}

variable "aws_region" {
  description = "AWS region for the example deployment."
  type        = string
  default     = "eu-central-1"
}

