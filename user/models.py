from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# Custom User Manager
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
        user.save(using=self._db)
        return user


# Custom User Model
class Account(AbstractBaseUser):
    DESIGNATION_CHOICES = [
        ('iCT', 'ICT'),
        ('TEA GIRL', 'TEA GIRL'),
        ('CUSTOMER CARE', 'CUSTOMER CARE'),
        ('GENERAL DUTIES', 'GENERAL DUTIES'),
        ('SUPPORT STAFF', 'SUPPORT STAFF'),
    ]
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=80)
    id_number = models.CharField(max_length=20, unique=True, null=True)
    personal_number = models.CharField(max_length=20, unique=True, null=True)
    designation = models.CharField(max_length=50,choices=DESIGNATION_CHOICES,null=True,blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')],null=True,
    )
    profile_picture = models.ImageField(upload_to='profile_pictures', blank=True)
    email = models.EmailField(max_length=110, unique=True)
    username = models.CharField(max_length=50, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    total_leave_days = models.IntegerField(default=0)

    huduma_centre = models.CharField(max_length=100, verbose_name="Huduma Centre", blank=True)
    supervisor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='supervised_employees')



    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = AccountManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True


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

    def __str__(self):
        return f"{self.employee.username} - {self.get_leave_type_display()} ({self.status})"
