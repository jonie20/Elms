from django.contrib import admin
from django.contrib.auth.models import Group
from user.models import Account, LeaveApplication, HudumaCentre, Holiday


class LeaveApplicationAdmin(admin.ModelAdmin):
    readonly_fields = ('from_date', 'to_date', 'leave_type', 'description', 'employee')  # Make fields read-only
    list_display = ('employee', 'from_date', 'to_date', 'leave_type', 'status', 'description')
    list_filter = ('status', 'leave_type', 'employee__huduma_centre')  # Add filter by HudumaCentre
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__username')

    def get_queryset(self, request):
        """Customize the queryset based on user role."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_CEO:
            return qs  # CEO or superusers see all leave applications
        elif request.user.is_manager:
            # Managers see only leave applications for their station
            return qs.filter(employee__huduma_centre=request.user.huduma_centre)
        return qs.none()  # Default: no access for other users

    def has_change_permission(self, request, obj=None):
        """Restrict managers to modifying leave applications only from their station."""
        if request.user.is_superuser or request.user.is_CEO:
            return True
        if request.user.is_manager and obj:
            return obj.employee.huduma_centre == request.user.huduma_centre
        return False

    def save_model(self, request, obj, form, change):
        """Prevent editing certain fields during updates."""
        if change:
            original = LeaveApplication.objects.get(pk=obj.pk)
            obj.from_date = original.from_date
            obj.to_date = original.to_date
            obj.leave_type = original.leave_type
            obj.description = original.description
        super().save_model(request, obj, form, change)


admin.site.register(LeaveApplication, LeaveApplicationAdmin)


class AccountAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'id_number', 'personal_number', 'huduma_centre', 'designation', 'gender', 'total_leave_days')
    search_fields = ('first_name', 'last_name', 'id_number', 'personal_number', 'designation')
    list_filter = ('gender', 'designation', 'huduma_centre')
    ordering = ('first_name', 'last_name')


admin.site.register(Account, AccountAdmin)


class HudumaCentreAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')


admin.site.register(HudumaCentre, HudumaCentreAdmin)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'holiday_date')  # Display the name and holiday date
    search_fields = ('name',)  # Allow searching by name

admin.site.register(Holiday, HolidayAdmin)