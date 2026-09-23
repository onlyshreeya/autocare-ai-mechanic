from django.db import models

# Create your models here.
class ChatMessage(models.Model):
    user_message = models.TextField()
    bot_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user_message

class MediaUpload(models.Model):
    MEDIA_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
    ]

    file = models.FileField(upload_to="uploads/")
    original_filename = models.CharField(max_length=255)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename
    
class Diagnosis(models.Model):
    vehicle_model = models.CharField(max_length=100, blank=True)
    symptoms = models.TextField()
    diagnosis_result = models.TextField()
    severity = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.symptoms[:50]
    
class Booking(models.Model):
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    vehicle_model = models.CharField(max_length=100)
    issue_description = models.TextField()
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.appointment_date}"