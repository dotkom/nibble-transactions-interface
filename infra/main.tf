variable "topic_name" {
  type    = string
}

variable "subscription_name" {
  type    = string
}

variable "push_endpoint" {
  type    = string
}

resource "google_pubsub_topic" "this" {
  name = var.topic_name
  message_retention_duration = "86600s"
}

resource "google_pubsub_subscription" "this" {
  name  = var.subscription_name
  topic = google_pubsub_topic.this.id

  ack_deadline_seconds = 20

  push_config {
    push_endpoint = var.push_endpoint

    attributes = {
      x-goog-version = "v1"
    }
  }
}
