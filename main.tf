terraform {
  # We're using the value_wo featuers that exist in TF 1.11 or later
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}

module "function" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.0"

  function_name = "feedsummarizer-${var.environment}"
  description   = "Slack RSS Feed Summarizer"
  runtime       = "python3.13"
  handler       = "summarizer.lambda_handler"
  timeout       = 300 # 5 minutes

  build_in_docker = true
  architectures   = [var.architecture]

  source_path = [{
    path             = "${path.module}/src"
    pip_requirements = true
    dockerize_pip    = true
  }]

  environment_variables = {
    BEDROCK_MODEL = var.bedrock_model

    PARAM_SLACK_WEBHOOK = aws_ssm_parameter.webhook_url.name

    POWERTOOLS_LOG_LEVEL    = var.log_level
    POWERTOOLS_SERVICE_NAME = "feedsummarizer"
  }

  attach_policy_statements = true
  policy_statements = {
    AllowBedrock = {
      effect    = "Allow"
      actions   = ["bedrock:InvokeModel"]
      resources = ["*"] # TODO: Lock down to just the selected model
    }

    AllowSsmParameters = {
      effect  = "Allow"
      actions = ["ssm:GetParameter"]
      resources = [
        aws_ssm_parameter.webhook_url.arn,
      ]
    }
  }
}

resource "aws_ssm_parameter" "webhook_url" {
  name = "/feedsummarizer/${var.environment}/slack-webhook-url"
  type = "SecureString"

  # Seed value
  value_wo         = "not-set"
  value_wo_version = 1
}

module "scheduler_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role"
  version = "5.58.0"

  trusted_role_services = ["scheduler.amazonaws.com"]

  create_role       = true
  role_requires_mfa = false # This is a service role, not for humans
  role_name         = "feedsummarizer-${var.environment}-scheduler"

  inline_policy_statements = [{
    sid = "AllowTriggerLambda"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [module.function.lambda_function_arn]
  }]
}

resource "aws_scheduler_schedule" "this" {
  name                         = "feedsummarizer-${var.environment}"
  schedule_expression          = var.schedule_expression
  schedule_expression_timezone = var.schedule_expression_timezone

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = module.function.lambda_function_arn
    role_arn = module.scheduler_role.iam_role_arn
  }
}
