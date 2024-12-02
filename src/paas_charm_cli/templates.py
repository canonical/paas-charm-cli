MAIN_TF = """
terraform {
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

resource "juju_application" "ingress" {
  name = "nginx-ingress-integrator"

  model = juju_model.{{ model_resource_name }}.name

  charm {
    name = "nginx-ingress-integrator"
  }

  units = 1
}

resource "juju_integration" "app_to_ingress" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = "{{ app_name }}"
    endpoint = "ingress"
  }

  application {
    name     = juju_application.ingress.name
    endpoint = "ingress"
  }
}
"""
