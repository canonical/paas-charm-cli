variable "image_registry" {
  type = string
}

variable "app" {
  type = object({
    units = number
  })
}

variable "ingress" {
  type = object({
    config = object({
      service-hostname = string,
      path-routes      = string,
    })
  })
}

variable "model" {
  type = object({
    name = string
    cloud = object({
      name   = string
      region = string
    })
  })
}
