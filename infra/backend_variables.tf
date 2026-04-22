variable "app_name" {
  description = "Nombre base de la aplicacion backend para recursos ECS/ALB."
  type        = string
  default     = "movilidad-backend"
}

variable "container_port" {
  description = "Puerto del contenedor FastAPI."
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU para la tarea Fargate (256, 512, 1024, etc.)."
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memoria (MiB) para la tarea Fargate (512, 1024, etc.)."
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Numero deseado de tareas ECS para el backend."
  type        = number
  default     = 1
}

variable "app_database_url" {
  description = "Valor para APP_DATABASE_URL. La base de datos se provee fuera de este modulo."
  type        = string
  sensitive   = true
}

variable "app_cors_allowed_origins" {
  description = "Valor para APP_CORS_ALLOWED_ORIGINS en el contenedor."
  type        = string
  default     = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
}

variable "backend_extra_environment" {
  description = "Variables adicionales para el contenedor backend (name => value)."
  type        = map(string)
  default     = {}
}

variable "health_check_path" {
  description = "Ruta del health check del backend expuesta por FastAPI."
  type        = string
  default     = "/health"
}

variable "assign_public_ip" {
  description = "Asigna IP publica a tareas Fargate (util en subredes publicas sin NAT)."
  type        = bool
  default     = true
}

variable "alb_ingress_cidr_blocks" {
  description = "CIDRs permitidos hacia el ALB en HTTP (80)."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}