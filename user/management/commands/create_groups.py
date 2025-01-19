# accounts/management/commands/create_groups.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Create user groups and assign permissions'

    def handle(self, *args, **kwargs):
        # Create groups
        admin_group, created = Group.objects.get_or_create(name='Admin')
        ceo_group, created = Group.objects.get_or_create(name='CEO')
        manager_group, created = Group.objects.get_or_create(name='Manager')
        staff_group, created = Group.objects.get_or_create(name='Staff')

        # Assign permissions to groups
        # Example: Add all permissions to Admin group
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)

        # Example: Add specific permissions to CEO group
        ceo_permissions = Permission.objects.filter(codename__in=['add_user', 'change_user', 'delete_user'])
        ceo_group.permissions.set(ceo_permissions)

        # Example: Add specific permissions to Manager group
        manager_permissions = Permission.objects.filter(codename__in=['add_user', 'change_user'])
        manager_group.permissions.set(manager_permissions)

        # Example: Add specific permissions to Staff group
        staff_permissions = Permission.objects.filter(codename__in=['view_user'])
        staff_group.permissions.set(staff_permissions)

        self.stdout.write(self.style.SUCCESS('Successfully created user groups and assigned permissions'))