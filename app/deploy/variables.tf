variable "image_registry" {
  type = string
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
