# Get the lambda functions
variable "scrapper_lambda_arn" {}
variable "transformer_lambda_arn" {}

# AWS Step function role
resource "aws_iam_role" "step_function_role" {
    name = "nike_step_function_role"
    assume_role_policy = <<-EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "states.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": "StepFunctionAssumeRole"
            }
        ]
    }
    EOF
}

# AWS Step function role-policy
resource "aws_iam_role_policy" "nike_step_function_policy" {
    name = "nike_step_function-policy"
    role = aws_iam_role.step_function_role.id
    policy = <<-EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Effect": "Allow",
                "Resource": [
                    "${var.scrapper_lambda_arn}",
                    "${var.transformer_lambda_arn}"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogDelivery",
                    "logs:GetLogDelivery",
                    "logs:UpdateLogDelivery",
                    "logs:DeleteLogDelivery",
                    "logs:ListLogDeliveries",
                    "logs:PutResourcePolicy",
                    "logs:DescribeResourcePolicies",
                    "logs:DescribeLogGroups"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                "Resource": [
                    "*"
                ]
            }
        ]
    }
    EOF
}

# AWS State function - State machine
resource "aws_sfn_state_machine" "sfn_state_machine" {
    name = "Nike-Project-State-Machine"
    role_arn = aws_iam_role.step_function_role.arn

    definition = <<EOF
    {
        "Comment": "A description of my state machine",
        "StartAt": "Run Scraper",
        "States": {
            "Run Scraper": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "OutputPath": "$.Payload",
            "Parameters": {
                "FunctionName": "${var.scrapper_lambda_arn}",
                "Payload": {
                "max_pages": 10,
                "day_count": 0,
                "min_sales": 0,
                "max_sales": 4
                }
            },
            "Retry": [
                {
                "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                ],
                "IntervalSeconds": 1,
                "MaxAttempts": 3,
                "BackoffRate": 2
                }
            ],
            "Next": "Transform Step"
            },
            "Transform Step": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "OutputPath": "$.Payload",
            "Parameters": {
                "Payload.$": "$",
                "FunctionName": "${var.transformer_lambda_arn}"
            },
            "Retry": [
                {
                "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                ],
                "IntervalSeconds": 1,
                "MaxAttempts": 3,
                "BackoffRate": 2
                }
            ],
            "End": true
            }
        }
    }
    EOF
}

output "state_machine_arn" {
    value = aws_sfn_state_machine.sfn_state_machine.arn
}