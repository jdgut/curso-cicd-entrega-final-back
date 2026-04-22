output "backend_alb_dns_name" {
  description = "DNS Name del Application Load Balancer del backend"
  value       = aws_lb.backend.dns_name
}

output "backend_alb_url" {
  description = "URL completa del ALB del backend (con http://)"
  value       = "http://${aws_lb.backend.dns_name}/"
}

output "backend_ecs_cluster_name" {
  description = "Nombre del ECS Cluster del backend"
  value       = aws_ecs_cluster.backend.name
}

output "backend_ecs_service_name" {
  description = "Nombre del ECS Service del backend"
  value       = aws_ecs_service.backend.name
}

output "backend_ecs_task_definition_arn" {
  description = "ARN de la task definition activa del backend"
  value       = aws_ecs_task_definition.backend.arn
}