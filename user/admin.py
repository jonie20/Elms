from django.contrib import admin
from user.models import Account, LeaveApplication

admin.site.register(Account)
class LeaveApplicationAdmin(admin.ModelAdmin):
    readonly_fields = ('from_date', 'to_date', 'leave_type', 'description','employee')  # Make fields read-only

    def save_model(self, request, obj, form, change):
        if change:  # When editing an existing leave application
            original = LeaveApplication.objects.get(pk=obj.pk)
            # Prevent date changes
            obj.from_date = original.from_date
            obj.to_date = original.to_date
            obj.leave_type = original.leave_type
            obj.description = original.description
        super().save_model(request, obj, form, change)

admin.site.register(LeaveApplication, LeaveApplicationAdmin)