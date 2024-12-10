from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have Email address")
        if not username:
            raise ValueError("Users must have Username")
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

class Account(AbstractBaseUser):
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=80)
    profile_picture = models.ImageField(upload_to='profile_pictures', blank=True)
    email = models.EmailField(max_length=110, unique=True)
    username = models.CharField(max_length=50, unique=True)
    date_joined = models.DateTimeField(verbose_name='user date joined',auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login',auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email',]

    objects = AccountManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.username}'

    def has_perm(self, perm, obj=None):
        return self.is_admin
    def has_module_perms(self, app_label):
        return True

class LeaveApplication(models.Model):
    LEAVE_TYPES = [
        ('SL', 'Sick Leave'),
        ('CL', 'Casual Leave'),
        ('PL', 'Paid Leave'),
        ('EL', 'Emergency Leave'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    leave_type = models.CharField(max_length=2, choices=LEAVE_TYPES, verbose_name="Leave Type")
    from_date = models.DateField(verbose_name="From Date")
    to_date = models.DateField(verbose_name="To Date")
    description = models.TextField(verbose_name="Description")
    posting_date = models.DateTimeField(auto_now_add=True, verbose_name="Posting Date")
    admin_remarks = models.TextField(null=True, blank=True, verbose_name="Admin Remarks")
    admin_remark_date = models.DateTimeField(null=True,auto_now_add=True, verbose_name="admin date")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending', verbose_name="Status")
    employee = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Employee")

    def __str__(self):
        return f"{self.employee.username} - {self.get_leave_type_display()} ({self.status})"
