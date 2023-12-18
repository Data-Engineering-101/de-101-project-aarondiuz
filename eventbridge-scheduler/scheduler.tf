variable "stepfunction_arn" {}

# AWS Step function role
resource "aws_iam_role" "eventbridge_scheduler_role" {
    name = "nike_eventbridge_scheduler_role"
    assume_role_policy = <<-EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "scheduler.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": "693071886825"
                    }
                }
            }
        ]
    }
    EOF
}

# AWS Step function role-policy
resource "aws_iam_role_policy" "nike_eventbridge_scheduler_policy" {
    name = "nike_eventbridge_scheduler-policy"
    role = aws_iam_role.eventbridge_scheduler_role.id
    policy = <<-EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "states:StartExecution"
                ],
                "Resource": [
                    "${var.stepfunction_arn}"
                ]
            }
        ]
    }
    EOF
}

resource "aws_scheduler_schedule" "trigger" {
  name       = "Nike-Project-Scheduler"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 days)"
  start_date = "2023-12-18T17:50:00-06:00"

  target {
    arn      = "${var.stepfunction_arn}"
    role_arn = aws_iam_role.eventbridge_scheduler_role.arn
  }
}