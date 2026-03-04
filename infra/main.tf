provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Create a place to store your Docker images
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "aia-auditor-repo"
  format        = "DOCKER"
}


# 2. The Backend (CPU Only - Free Tier Friendly)
resource "google_cloud_run_v2_service" "backend" {
  name     = "aia-backend"
  location = var.region

  template {
    scaling {
      min_instance_count = 0 # Scales to $0 when not in use
      max_instance_count = 1 
    }
    containers {
      # This points to the image we will push in the next step
      image = "${var.region}-docker.pkg.dev/${var.project_id}/aia-auditor-repo/backend:latest"
      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
        cpu_idle = true # Only pays when processing a request
      }
      env {
        name  = "OLLAMA_HOST"
        value = "http://localhost:11434"
      }
    }
  }
}

# 3. Allow the public to see the app
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}