from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Board(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(CustomUser, related_name='boards', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invite_token = models.UUIDField(null=True, blank=True, unique=True )

    def __str__(self):
        return self.name

    def create_default_columns(self):
        """Создает три колонки по умолчанию для доски."""
        COLORS = ['#61bd4f', '#f2d600', '#ff9f1a']  # Пример цветов
        columns_data = [
            {'name': 'Нужно сделать', 'color': COLORS[0]},
            {'name': 'В процессе', 'color': COLORS[1]},
            {'name': 'Готово', 'color': COLORS[2]},
        ]
        for data in columns_data:
            Column.objects.create(board=self, **data)

class BoardMember(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Владелец'),
        ('member', 'Участник'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'board')

class Column(models.Model):
    board = models.ForeignKey(Board, related_name='columns', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#ffffff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.board.name} - {self.name}"

class Task(models.Model):
    column = models.ForeignKey(Column, related_name='tasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.column.name} - {self.name}"

class SubTask(models.Model):
    task = models.ForeignKey(Task, related_name='subtasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task.name} - {self.name}"

class TaskMember(models.Model):
    task = models.ForeignKey(Task, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'user')

class FileAttachment(models.Model):
    task = models.ForeignKey(Task, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name