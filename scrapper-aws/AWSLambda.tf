# IAM role for lambda
resource "aws_iam_role" "lambda_role" {
    name = "scrapper_lambda_role"
    assume_role_policy = file("scrapper-aws/lambda_assume_role_policy.json")
}

# IAM role-policy for lambda
resource "aws_iam_role_policy" "lambda_policy" {
    name = "scrapper_lambda_policy"
    role = aws_iam_role.lambda_role.id
    policy = file("scrapper-aws/lambda_policy.json")
}

# Create a zip archive from the source code directory
data "archive_file" "origin_request_lambda_source" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-files"  # Path to the source code directory
  output_path = "${path.module}/scrapper.zip"
}

# Define the AWS Lambda function resource
resource "aws_lambda_function" "test_lambda" {
  function_name = "Enroute-Nike-Scrapper"  # Name of the Lambda function
  handler      = "main.lambda_handler"  # Handler for the Lambda function
  role         = aws_iam_role.lambda_role.arn  # IAM role for the Lambda function
  runtime      = "python3.11"  # Python runtime version
  source_code_hash = data.archive_file.origin_request_lambda_source.output_base64sha256  # Hash of the source code
  filename     = data.archive_file.origin_request_lambda_source.output_path  # Path to the Lambda deployment package
  timeout      = 600  # Maximum execution time for the Lambda function (in seconds)
  memory_size  = 2048  # Memory allocated to the Lambda function (in MB)
  layers = ["arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-pandas:5", "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-beautifulsoup4:2", "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-requests:4", "arn:aws:lambda:us-east-1:693071886825:layer:tqdm:1"]
  environment {
    variables = {
      BUCKET_NAME = "enroute-project"  # Environment variables for the Lambda function
    }
  }
}

# Output to be consumed by other module
output "lambda_arn" {
  value = aws_lambda_function.test_lambda.arn
}