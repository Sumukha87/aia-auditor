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

# 2. The Backend (The AI Engine)
resource "google_cloud_run_v2_service" "backend" {
  name     = "aia-backend"
  location = var.region
  deletion_protection = false

  template {
    # 1. Give it more time to start (max is 3600, let's try 600s / 10 mins)
    timeout = "600s" 
    
    scaling {
      min_instance_count = 0 
      max_instance_count = 1 
    }
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/aia-auditor-repo/backend:latest"
      
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
        cpu_idle = true 
      }

      # 2. Explicitly tell Cloud Run which port to watch
      ports {
        container_port = 8080
      }

      env {
        name  = "QDRANT_URL"
        value = var.qdrant_url
      }
      env {
        name  = "QDRANT_API_KEY"
        value = var.qdrant_api_key
      }
      env {
        name  = "INTERNAL_API_KEY"
        value = var.internal_key
      }

      env {
        name  = "OLLAMA_HOST"
        value = "http://localhost:11434"
      }

      # 3. Add a Startup Probe (Wait for the container to be ready)
      startup_probe {
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 30 # 30 attempts * 10s = 5 minutes of grace
        tcp_socket {
          port = 8080
        }
      }
    }
  }
}

# 3. The Frontend (The User Interface)
resource "google_cloud_run_v2_service" "frontend" {
  name     = "aia-frontend"
  location = var.region
  deletion_protection = false

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/aia-auditor-repo/frontend:latest"
      
      # This hands the backend's secret URL to the frontend automatically!
      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      env {
        name  = "INTERNAL_API_KEY" # Make sure this matches the Backend env name
        value = var.internal_key
      }
      env {
        name  = "APP_PASSWORD"
        value = var.app_pass
      }
    }
  }
}

# 4. Make BOTH services public (One for API calls, one for the website)
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 5. Output the only URL you actually need to click
output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}