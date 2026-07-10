from django.db import models

class Interview(models.Model):
    LEVEL_CHOICES = [
        ('junior', 'Junior'),
        ('mid', 'Mid-Level'),
        ('senior', 'Senior'),
    ]
    topic = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='mid')
    summary = models.TextField(blank=True, null=True)
    sentiment = models.CharField(max_length=50, blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic} ({self.level}) - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class Question(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.IntegerField()

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"

class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer')
    text = models.TextField()

    def __str__(self):
        return f"Answer to Q{self.question.order}"