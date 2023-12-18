provider "aws" {
  profile = "default"
  region  = "us-east-1"
}

# Create AWS Python Lambda Function - Scrapper
module "scrapperLambdaFunction" {
  source = "./scrapper-aws"
}

# Create AWS Python Lambda Function - Transformer
module "transformerLambdaFunction" {
  source = "./transformer"
}

# Create AWS Stepfunction to Invoke AWS Lambda Functions
module "awsstepfunction" {
  source = "./stepfunction"
  scrapper_lambda_arn = module.scrapperLambdaFunction.lambda_arn
  transformer_lambda_arn = module.transformerLambdaFunction.lambda_arn
}

# Create EventBridge Scheduler
module "scheduler" {
  source = "./eventbridge-scheduler"
  stepfunction_arn = module.awsstepfunction.state_machine_arn
}