locals {
  resource_prefix = "${var.app_name}-${var.environment_name}"

  common_tags = {
    Environment = var.environment_name
    Service     = "backend"
  }
}

resource "aws_cloudwatch_log_group" "backend_ecs" {
  name              = "/ecs/${local.resource_prefix}-task"
  retention_in_days = 7

  tags = local.common_tags
}

resource "aws_ecs_cluster" "backend" {
  name = "${local.resource_prefix}-cluster"

  tags = local.common_tags
}