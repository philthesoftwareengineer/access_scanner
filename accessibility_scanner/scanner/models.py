from django.db import models

# Create your models here.


class AccessibilityResult(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    url = models.URLField(max_length=200)
    json_response = models.JSONField() 

    def __str__(self):
        return f"{self.timestamp} - {self.url}"