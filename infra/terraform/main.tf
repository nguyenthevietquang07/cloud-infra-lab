terraform {
  required_version = ">= 1.6.0"
}

variable "project_name" {
  type    = string
  default = "cloud-infra-lab"
}

# This skeleton documents intended cloud resources without provisioning by
# default. Add provider-specific modules only when deploying to a real account.
locals {
  service_name = var.project_name
  components = [
    "container_service",
    "managed_postgres",
    "managed_redis",
    "log_group",
    "health_check",
  ]
}

output "planned_components" {
  value = local.components
}
