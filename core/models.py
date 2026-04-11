from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    division = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    firebase_uid = models.CharField(max_length=255, blank=True, null=True, unique=True)

    class Meta:
        db_table = 'core_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.first_name or self.username or self.email


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return self.name


class UserTeaches(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userteaches')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='userteaches')
    proficiency = models.CharField(
        max_length=20,
        default='intermediate',
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ]
    )
    available_time = models.CharField(max_length=100, default='Flexible')
    notes = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'skill')
        verbose_name_plural = "User Teaches"

    def __str__(self):
        return f"{self.user.first_name} teaches {self.skill.name} ({self.proficiency})"


class ExchangeRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    PLATFORM_CHOICES = [
        ('google_meet', 'Google Meet'),
        ('teams', 'Microsoft Teams'),
    ]

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    offering_skill = models.CharField(max_length=100, help_text="What the requester offers in exchange")
    preferred_time = models.CharField(max_length=50, default='Flexible')
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    meeting_link = models.URLField(blank=True, null=True)
    meeting_platform = models.CharField(max_length=50, blank=True, null=True, choices=PLATFORM_CHOICES)
    scheduled_date = models.DateField(blank=True, null=True)
    scheduled_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Exchange Request'
        verbose_name_plural = 'Exchange Requests'

    def __str__(self):
        return f"{self.requester.first_name} → {self.receiver.first_name} ({self.skill.name})"
