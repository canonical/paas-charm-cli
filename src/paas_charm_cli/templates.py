MAIN_TF = """terraform {
  required_providers {
    juju = {
      version = "~> 0.13.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

resource "juju_model" "{{ model_resource_name }}" {
  name = var.model.name

  cloud {
    name   = var.model.cloud.name
    region = var.model.cloud.region
  }
}

resource "juju_application" "{{ app_name }}" {
  name = "{{ app_name }}"

  model = juju_model.{{ model_resource_name }}.name

  charm {
    name = "{{ app_name }}"
  }

  units = var.app.units
}

resource "juju_application" "ingress" {
  name = "nginx-ingress-integrator"

  model = juju_model.{{ model_resource_name }}.name

  charm {
    name = "nginx-ingress-integrator"
  }

  units = 1

  config = {
    service-hostname = var.ingress.config.service-hostname
    path-routes = var.ingress.config.path-routes
  }
}

resource "juju_integration" "app_to_ingress" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = juju_application.{{ app_name }}.name
    endpoint = "ingress"
  }

  application {
    name     = juju_application.ingress.name
    endpoint = "ingress"
  }
}
"""
