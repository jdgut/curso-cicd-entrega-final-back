# infra/demo_main.tf

terraform {
  required_version = ">= 1.6.0"
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Grupo de Logs para ECS ---
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/calculadora-${var.environment_name}-task"
  retention_in_days = 7

  tags = {
    Environment = var.environment_name
  }
}

# --- Cluster ECS ---
resource "aws_ecs_cluster" "main" {
  name = "calculadora-${var.environment_name}-cluster"

  tags = {
    Environment = var.environment_name
  }
}

# --- Seguridad ---
# Security Group para el Load Balancer (permite HTTP desde internet)
resource "aws_security_group" "alb_sg" {
  name        = "alb-sg-${var.environment_name}"
  description = "Permite trafico HTTP al ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP desde internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment_name
  }
}

# Security Group para el Servicio ECS (permite trafico desde el ALB en el puerto 8000)
resource "aws_security_group" "ecs_sg" {
  name        = "ecs-service-sg-${var.environment_name}"
  description = "Permite trafico desde el ALB al servicio ECS"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Trafico desde el ALB"
    from_port       = 8000 # Puerto del contenedor
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id] # Solo permite desde el ALB SG
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment_name
  }
}

# --- Load Balancer ---
resource "aws_lb" "main" {
  name               = "calculadora-${var.environment_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.subnet_ids # Debe estar en subredes publicas

  tags = {
    Environment = var.environment_name
  }
}

# Target Group para las tareas ECS
resource "aws_lb_target_group" "ecs_tg" {
  name        = "tg-ecs-${var.environment_name}"
  port        = 8000 # Puerto del contenedor
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip" # Necesario para Fargate

  health_check {
    enabled             = true
    path                = "/health" # Endpoint de health check de la app
    port                = "8000"    # Puerto del contenedor
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    timeout             = 5
    matcher             = "200"
  }

  tags = {
    Environment = var.environment_name
  }
}

# Listener HTTP en el puerto 80
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }
}

# --- Definición de Tarea ECS ---
resource "aws_ecs_task_definition" "app" {
  family                   = "calculadora-${var.environment_name}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"  # 0.25 vCPU (minimo Fargate)
  memory                   = "512"  # 0.5 GB (minimo Fargate)
  task_role_arn            = var.lab_role_arn       # Rol para permisos DENTRO del contenedor
  execution_role_arn       = var.lab_role_arn       # Rol para que ECS/Fargate pueda descargar imagen, enviar logs, etc.

  container_definitions = jsonencode([
    {
      name  = "calculadora-${var.environment_name}-container"
      image = var.docker_image_uri # Imagen de Docker Hub

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      # Variable de entorno inyectada al contenedor: clave secreta para Flask-WTF (CSRF).
      # El prefijo FLASK_ hace que from_prefixed_env() la recoja automáticamente como app.secret_key.
      environment = [
        {
          name  = "FLASK_SECRET_KEY"
          value = var.secret_key
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Environment = var.environment_name
  }
}

# --- Servicio ECS ---
resource "aws_ecs_service" "main" {
  name            = "calculadora-${var.environment_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1 # Numero inicial de tareas
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids # Las mismas subredes publicas del ALB
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true # Necesario en subredes publicas sin NAT Gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_tg.arn
    container_name   = "calculadora-${var.environment_name}-container"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 50  # Permite que baje al 50% durante el deploy
  deployment_maximum_percent         = 200 # Permite que suba al 200% temporalmente

  # Ignorar desired_count para permitir ajustes manuales sin reescribirlos en cada apply.
  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener.http] # Asegura que el listener exista antes de crear el servicio

  tags = {
    Environment = var.environment_name
  }
}