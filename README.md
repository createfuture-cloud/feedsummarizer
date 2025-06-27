# feedsummarizer

feedsummarizer is a tool to use Amazon Bedrock to summarize RSS Feeds -
specifically built with the AWS "What's New" feed in mind, as this can sometimes
receive over 25 posts per week.

## Deployment
This is designed currently to run as a Lambda in AWS, and this repository is a
terraform module which can deploy the Lambda & associated resources.

Once deployed, two further things must be configured:
* Enable access to the specified bedrock model. By default this is Claude Sonnet
  4 (EU).
* Update the SSM parameter with a Slack inbound webhook URL. This can be found
  at `/feedsummarizer/$ENVIRONMENT/slack-webhook-url`, and has a default value
  of `not-set`.


<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.11.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 5.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_function"></a> [function](#module\_function) | terraform-aws-modules/lambda/aws | 7.21.0 |
| <a name="module_scheduler_role"></a> [scheduler\_role](#module\_scheduler\_role) | terraform-aws-modules/iam/aws//modules/iam-assumable-role | 5.58.0 |

## Resources

| Name | Type |
|------|------|
| [aws_scheduler_schedule.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/scheduler_schedule) | resource |
| [aws_ssm_parameter.webhook_url](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_architecture"></a> [architecture](#input\_architecture) | CPU Architecture to Build & Deploy | `string` | `"x86_64"` | no |
| <a name="input_bedrock_model"></a> [bedrock\_model](#input\_bedrock\_model) | Which bedrock model ID to use | `string` | `"eu.anthropic.claude-sonnet-4-20250514-v1:0"` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment name to suffix to resources | `string` | `"prod"` | no |
| <a name="input_log_level"></a> [log\_level](#input\_log\_level) | Lambda Log Level | `string` | `"INFO"` | no |
| <a name="input_schedule_expression"></a> [schedule\_expression](#input\_schedule\_expression) | AWS EventBridge Scheduler Expression for when to run | `string` | `"cron(30 8 ? * FRI *)"` | no |
| <a name="input_schedule_expression_timezone"></a> [schedule\_expression\_timezone](#input\_schedule\_expression\_timezone) | Timezone for the schedule expression | `string` | `"UTC"` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->