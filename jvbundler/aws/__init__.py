"""AWS deployment modules for jvbundler.

Provides functionality for deploying jvagent applications to AWS Lambda,
including ECR, IAM, Lambda, and API Gateway management.
"""

from jvbundler.aws.lambda_deployer import LambdaDeployer

__all__ = ["LambdaDeployer"]
