variable "environment" {
  type        = string
  default     = "prod"
  description = "Environment name to suffix to resources"
}

variable "log_level" {
  type        = string
  default     = "INFO"
  description = "Lambda Log Level"
}

variable "bedrock_model" {
  default     = "eu.anthropic.claude-sonnet-4-20250514-v1:0"
  type        = string
  description = "Which bedrock model ID to use"
}

variable "schedule_expression" {
  type        = string
  description = "AWS EventBridge Scheduler Expression for when to run"
  default     = "cron(30 8 ? * FRI *)"
}

variable "schedule_expression_timezone" {
  type        = string
  description = "Timezone for the schedule expression"
  default     = "UTC"
}

variable "architecture" {
  type        = string
  description = "CPU Architecture to Build & Deploy"
  default     = "x86_64"
}
