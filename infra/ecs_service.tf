locals {
  container_name = "${local.resource_prefix}-container"

  base_backend_environment = {
    APP_APP_ENV              = var.environment_name
    APP_APP_HOST             = "0.0.0.0"
    APP_APP_PORT             = tostring(var.container_port)
    APP_DATABASE_URL         = var.app_database_url
    APP_CORS_ALLOWED_ORIGINS = var.app_cors_allowed_origins
  }

  effective_backend_environment = merge(local.base_backend_environment, var.backend_extra_environment)
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.resource_prefix}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  task_role_arn            = var.lab_role_arn
  execution_role_arn       = var.lab_role_arn

  container_definitions = jsonencode([
    {
      name  = local.container_name
      image = var.docker_image_uri

      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        for name, value in local.effective_backend_environment : {
          name  = name
          value = value
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend_ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_service" "backend" {
  name            = "${local.resource_prefix}-service"
  cluster         = aws_ecs_cluster.backend.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.backend_ecs_service.id]
    assign_public_ip = var.assign_public_ip
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = local.container_name
    container_port   = var.container_port
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener.backend_http]

  tags = local.common_tags
}