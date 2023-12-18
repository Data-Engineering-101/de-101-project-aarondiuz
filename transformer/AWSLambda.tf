# IAM role for lambda
resource "aws_iam_role" "lambda_role" {
    name = "scraper_lambda_role"
    assume_role_policy = file("transformer/lambda_assume_role_policy.json")
}

# IAM role-policy for lambda
resource "aws_iam_role_policy" "lambda_policy" {
    name = "scraper_lambda_policy"
    role = aws_iam_role.lambda_role.id
    policy = file("transformer/lambda_policy.json")
}

# Create a zip archive from the source code directory
data "archive_file" "origin_request_lambda_source" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-files"  # Path to the source code directory
  output_path = "${path.module}/transformer.zip"
}

# Define the AWS Lambda function resource
resource "aws_lambda_function" "test_lambda" {
  function_name = "Enroute-Nike-Transformer"  # Name of the Lambda function
  handler      = "transformer.lambda_handler"  # Handler for the Lambda function
  role         = aws_iam_role.lambda_role.arn  # IAM role for the Lambda function
  runtime      = "python3.11"  # Python runtime version
  source_code_hash = data.archive_file.origin_request_lambda_source.output_base64sha256  # Hash of the source code
  filename     = data.archive_file.origin_request_lambda_source.output_path  # Path to the Lambda deployment package
  timeout      = 60  # Maximum execution time for the Lambda function (in seconds)
  memory_size  = 1024  # Memory allocated to the Lambda function (in MB)
  layers = ["arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-pandas:5", "arn:aws:lambda:us-east-1:693071886825:layer:snowflake-connector-python:4"]
  environment {
    variables = {
      S3_BUCKET = "enroute-project"  # Environment variables for the Lambda function
      ACCOUNT = "AVB93148"
      DATABASE = "AWS_TEST"
      REGION = "us-east-1"
      SCHEMA = "PUBLIC"
      WAREHOUSE = "COMPUTE_WH"
    }
  }
}

# Output to be consumed by other module
output "lambda_arn" {
  value = aws_lambda_function.test_lambda.arn
}