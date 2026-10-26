from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ScrollSession(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='scroll_sessions')
    app_name=models.CharField(max_length=100)
    duration=models.PositiveIntegerField()
    scroll_count=models.PositiveIntegerField()
    momentum=models.CharField(max_length=20,choices=[('LOW', 'low'), ('MEDUIM', 'meduim'), ('HIGH', 'high'),])
    created_at=models.DateTimeField(auto_now_add=True)

class BreakEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=100)
    duration = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.app_name} break - {self.duration}s"

class UserGoal(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="scroll_goal"
    )
    daily_limit_minutes = models.PositiveIntegerField(default=60)

    def __str__(self):
        return f"{self.user.username} - {self.daily_limit_minutes} min/day"