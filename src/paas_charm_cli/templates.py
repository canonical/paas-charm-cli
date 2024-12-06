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

resource "juju_application" "prometheus-k8s" {
  name = "prometheus-k8s"

  model = juju_model.{{ model_resource_name }}.name

  charm {
    name = "prometheus-k8s"
  }

  units = 1
}

resource "juju_integration" "app_to_prometheus" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = juju_application.{{ app_name }}.name
    endpoint = "metrics-endpoint"
  }

  application {
    name     = juju_application.prometheus-k8s.name
    endpoint = "metrics-endpoint"
  }
}

resource "juju_application" "loki-k8s" {
  name = "loki-k8s"

  model = juju_model.{{ model_resource_name }}.name

  charm {
    name = "loki-k8s"
  }

  units = 1
}

resource "juju_integration" "app_to_loki" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = juju_application.{{ app_name }}.name
    endpoint = "logging"
  }

  application {
    name     = juju_application.loki-k8s.name
    endpoint = "logging"
  }
}

resource "juju_application" "grafana-k8s" {
  name = "grafana-k8s"

  model = juju_model.{{ model_resource_name }}.name

  charm {
    name = "grafana-k8s"
  }

  units = 1
}

resource "juju_integration" "prometheus_to_grafana" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = juju_application.prometheus-k8s.name
    endpoint = "grafana-source"
  }

  application {
    name     = juju_application.grafana-k8s.name
    endpoint = "grafana-source"
  }
}

resource "juju_integration" "loki_to_grafana" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = juju_application.loki-k8s.name
    endpoint = "grafana-source"
  }

  application {
    name     = juju_application.grafana-k8s.name
    endpoint = "grafana-source"
  }
}

resource "juju_integration" "app_to_grafana" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = juju_application.{{ app_name }}.name
    endpoint = "grafana-dashboard"
  }

  application {
    name     = juju_application.grafana-k8s.name
    endpoint = "grafana-dashboard"
  }
}{{ postgres_k8s_tf }}
"""
POSTGRES_K8S_TF = """

resource "juju_application" "postgresql-k8s" {
  name = "postgresql-k8s"

  model = juju_model.{{ model_resource_name }}.name

  charm {
    name = "postgresql-k8s"
  }

  trust = true

  units = 1
}

resource "juju_integration" "app_to_postgresql" {
  model = juju_model.{{ model_resource_name }}.name

  application {
    name     = juju_application.{{ app_name }}.name
    endpoint = "postgresql"
  }

  application {
    name     = juju_application.postgresql-k8s.name
    endpoint = "database"
  }
}"""
