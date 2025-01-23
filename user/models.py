import os
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission


# Function to generate a unique name for profile picture uploads
def generate_unique_name(instance, filename):
    name = uuid.uuid4()
    full_file_name = f'{name}-{filename}'
    return os.path.join('profile_pictures', full_file_name)


class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an Email address")
        if not username:
            raise ValueError("Users must have a Username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.is_CEO = True
        user.is_manager = True
        user.save(using=self._db)
        return user


# HudumaCentre Model
class HudumaCentre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Account(AbstractBaseUser, PermissionsMixin):
    DESIGNATION_CHOICES = [
        ('ICT', 'ICT'),
        ('TEA GIRL', 'TEA GIRL'),
        ('CUSTOMER CARE', 'CUSTOMER CARE'),
        ('GENERAL DUTIES', 'GENERAL DUTIES'),
        ('SUPPORT STAFF', 'SUPPORT STAFF'),
    ]
    huduma_centre = models.ForeignKey(
        HudumaCentre,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
        verbose_name="Huduma Centre")

    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=80)
    id_number = models.CharField(max_length=20, unique=True, null=True)
    personal_number = models.CharField(max_length=20, unique=True, null=True)
    phone_number = models.CharField(max_length=10, null=True)
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES, null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')], null=True,
    )
    profile_picture = models.ImageField(upload_to=generate_unique_name, blank=True)
    email = models.EmailField(max_length=110, unique=True)
    username = models.CharField(max_length=50, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_CEO = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    sick_leave_days = models.IntegerField(default=15)
    casual_leave_days = models.IntegerField(default=10)
    emergency_leave_days = models.IntegerField(default=5)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = AccountManager()

    @property
    def total_leave_days(self):
        return self.sick_leave_days + self.casual_leave_days + self.emergency_leave_days

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

class Holiday(models.Model):
    name = models.CharField(max_length=255)
    holiday_date = models.DateField()

    def _str_(self):
        return f"{self.name} on {self.holiday_date}"

    class Meta:
        verbose_name = "Holiday"
        verbose_name_plural = "Holidays"

# Leave Application Model
class LeaveApplication(models.Model):
    LEAVE_TYPES = [
        ('SL', 'Sick Leave'),
        ('CL', 'Casual Leave'),
        ('EL', 'Emergency Leave'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    leave_type = models.CharField(max_length=2, choices=LEAVE_TYPES)
    from_date = models.DateField()
    to_date = models.DateField()
    description = models.TextField()
    posting_date = models.DateTimeField(auto_now_add=True)
    admin_remarks = models.TextField(null=True, blank=True)
    admin_remark_date = models.DateField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    employee = models.ForeignKey(Account, on_delete=models.CASCADE)
    no_of_days = models.IntegerField(verbose_name="Number of Days", default=15)
    carry_forward_days = models.IntegerField(verbose_name="Carry Forward Days", default=0)
    total_leave_days = models.IntegerField(verbose_name="Total Leave Days", default=0)

    def clean(self):
        super().clean()
        if self.from_date < datetime.now().date():
            raise ValueError("Start date cannot be in the past.")
        if self.to_date < self.from_date:
            raise ValueError("End date cannot be earlier than the start date.")

    def calculate_working_days(self):
        holidays = Holiday.objects.values_list('holiday_date', flat=True)
        total_days = 0
        current_date = self.from_date

        while current_date <= self.to_date:
            # Exclude weekends (Saturday=5, Sunday=6) and holidays
            if current_date.weekday() < 5 and current_date not in holidays:
                total_days += 1
            current_date += timedelta(days=1)

        return total_days


    def save(self, *args, **kwargs):
        self.no_of_days = self.calculate_working_days()
        super().save(*args, **kwargs)

    def _str_(self):
        return f"{self.employee.username} - {self.get_leave_type_display()} ({self.status})"


