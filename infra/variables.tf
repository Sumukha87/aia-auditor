variable "project_id" { type = string }
variable "region"     { default = "us-central1" } # Best for Free Tier
variable "app_pass"   { type = string }
variable "qdrant_url" { type = string }
variable "qdrant_api_key" { type = string }
variable "internal_key" { type = string }