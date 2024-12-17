from django.contrib import admin
from user.models import Account, LeaveApplication,HudumaCentre





class LeaveApplicationAdmin(admin.ModelAdmin):
    readonly_fields = ('from_date', 'to_date', 'leave_type', 'description', 'employee')  # Make fields read-only
    list_display = ('employee','from_date', 'to_date', 'leave_type', 'description')

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


class AccountAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('first_name', 'last_name', 'id_number', 'personal_number', 'designation', 'gender','total_leave_days','huduma_centre')

    # Fields that are searchable in the admin
    search_fields = ('first_name', 'last_name', 'id_number', 'personal_number', 'designation')

    # Fields to filter in the admin
    list_filter = ('gender', 'designation')

    ordering = ('first_name', 'last_name')
admin.site.register(Account,AccountAdmin)
class HudumaCentreAdmin(admin.ModelAdmin):
    list_display = ('location','name')
admin.site.register(HudumaCentre,HudumaCentreAdmin)