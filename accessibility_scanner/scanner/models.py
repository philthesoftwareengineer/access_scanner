from django.db import models

# Create your models here.


class AccessibilityResult(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    url = models.URLField(max_length=200)
    status = models.CharField(max_length=50)
    message = models.TextField()

    def __str__(self):
        return f"{self.timestamp} - {self.url} - {self.status}"