from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View

from user.authentication import AccountAuthentication
from user.forms import GroupForm, AssignGroupForm
from user.models import Account, LeaveApplication, HudumaCentre


def group_required(*group_names):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name__in=group_names).exists() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied

        return _wrapped_view

    return decorator


def manage_groups(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()  # Simply save the form
            return redirect('manage_groups')  # Redirect after saving
    else:
        form = GroupForm()

    groups = Group.objects.all()
    return render(request, 'board/manage_groups.html', {'form': form, 'groups': groups})



def assign_group(request):
    if request.method == 'POST':
        form = AssignGroupForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            group = form.cleaned_data['group']
            user.groups.add(group)
            return redirect('assign_group')
    else:
        form = AssignGroupForm()
    return render(request, 'board/assign_group.html', {'form': form})

# noinspection PyMethodMayBeStatic
class RegisterView(View):
    def get(self, request):

        return render(request, 'board/employee.html', {
            'huduma_centre': HudumaCentre.objects.all()  # Provide all Huduma Centres to the template
        })

    def post(self, request):
        # Get the selected Huduma Centre
        huduma_centre_id = request.POST.get('huduma_centre')

        # If no Huduma Centre is selected, return with error message
        if not huduma_centre_id:
            messages.error(request, "Please select a Huduma Centre.")
            return redirect('register')  # Redirect back to the registration form (ensure this matches your URL name)

        try:
            # Retrieve the selected Huduma Centre
            huduma_centre = HudumaCentre.objects.get(id=huduma_centre_id)
        except HudumaCentre.DoesNotExist:
            messages.error(request, "The selected Huduma Centre does not exist.")
            return redirect('register')  # Redirect back to the registration form

        # Automatically set username to be the same as the first name
        username = request.POST.get('first_name').lower()  # Use the lowercase of the first name as the username

        # Check if the username already exists
        if Account.objects.filter(username=username).exists():
            messages.error(request, "This username already exists. Please choose another one.")
            return redirect('register')  # Redirect back to the registration form

        # Create Account model using the form data
        account_model = Account.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            personal_number=request.POST.get('personal_number'),
            profile_picture=request.FILES.get('profile_picture'),  # Handle file upload correctly
            gender=request.POST.get('gender'),
            phone_number=request.POST.get('phone_number'),
            id_number=request.POST.get('id_number'),
            username=username,  # Set the username to first name
            huduma_centre=huduma_centre,
        )

        # Set password and save the account model
        account_model.set_password(request.POST.get('password1'))
        account_model.save()

        # Redirect to the dashboard without logging the user in
        messages.success(request, "Registration successful! You can now log in.")
        return redirect('dashboard')  # Redirect to the dashboard after successful registration

# noinspection PyMethodMayBeStatic
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password1')
        user = AccountAuthentication.authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            # Redirect based on user's role or permissions
            if user.is_superuser or user.is_admin or user.is_manager or user.is_CEO:  # For admin users
                return redirect('/accounts/board')
            else:  # For regular users
                return redirect('dash')  # Ensure 'dash' is defined in urls.py

        else:
            messages.error(request, "Invalid email or password. Please try again.")
            return redirect('login-view')  # Ensure 'login-view' is defined in urls.py

# noinspection PyMethodMayBeStatic
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login-view')

# noinspection PyMethodMayBeStatic

class DashView(View):
    def get(self, request):
        # Retrieve all leave applications for the user
        leave_applications = LeaveApplication.objects.filter(employee=request.user).order_by('-posting_date')

        # Calculate dynamic values
        carry_forward_days = leave_applications.filter(
            status="Approved", to_date__lt=datetime.now().date()
        ).count()  # Replace with actual carry-forward logic

        leave_allocated = 15  # Example value; replace with actual allocation logic
        total_leave_days = carry_forward_days + leave_allocated

        # Pass data to template
        context = {
            'leave_applications': leave_applications,
            'status_filter': request.GET.get('status', 'all'),
            'dashboard_data': {
                'financial_year': '2024/2025',  # Hardcoded
                'carry_forward': carry_forward_days,
                'leave_allocated': leave_allocated,
                'total_leave_days': total_leave_days,
            }
        }
        return render(request, 'index.html', context)


@login_required
def apply_leave(request):
    user = request.user
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        description = request.POST.get('description')

        if LeaveApplication.objects.filter(employee=user, status='Pending').exists():
            messages.error(request, "You cannot apply for leave while a previous application is pending.")
            return redirect('apply_leave')

        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format. Please try again.")
            return redirect('apply_leave')

        current_date = datetime.now().date()
        max_date = current_date + timedelta(days=15)

        if not leave_type or not description:
            messages.error(request, "All fields are required. Please try again.")
            return redirect('apply_leave')
        elif from_date_obj < current_date:
            messages.error(request, "Start date cannot be in the past. Please select a valid date.")
            return redirect('apply_leave')
        elif from_date_obj > max_date:
            messages.error(request, "Start date cannot be more than 1 month from today.")
            return redirect('apply_leave')
        elif to_date_obj < from_date_obj:
            messages.error(request, "End date cannot be earlier than the start date.")
            return redirect('apply_leave')

        leave_application = LeaveApplication(
            leave_type=leave_type,
            from_date=from_date_obj,
            to_date=to_date_obj,
            description=description,
            employee=user,
        )

        # Calculate the number of working days (excluding weekends and holidays)
        leave_application.no_of_days = leave_application.calculate_working_days()

        # Check if the user has enough leave days for the specific leave type
        if leave_type == 'SL' and leave_application.no_of_days > user.sick_leave_days:
            messages.error(request, "You do not have enough sick leave days available.")
            return redirect('apply_leave')
        elif leave_type == 'CL' and leave_application.no_of_days > user.casual_leave_days:
            messages.error(request, "You do not have enough casual leave days available.")
            return redirect('apply_leave')
        elif leave_type == 'EL' and leave_application.no_of_days > user.emergency_leave_days:
            messages.error(request, "You do not have enough emergency leave days available.")
            return redirect('apply_leave')

        leave_application.save()

        messages.success(request, "Leave application submitted successfully.")
        return redirect('dash')  # Redirect to user's dashboard or any relevant page

    context = {
        'total_leave_days': user.total_leave_days,
        'sick_leave_days': user.sick_leave_days,
        'casual_leave_days': user.casual_leave_days,
        'emergency_leave_days': user.emergency_leave_days,
    }
    return render(request, 'apply_leave.html', context)


@login_required
def leavehistory(request):
    status_filter = request.GET.get('status', 'all')

    if status_filter == 'all':
        leave_applications = LeaveApplication.objects.filter(employee=request.user).order_by('-posting_date')
    else:
        leave_applications = LeaveApplication.objects.filter(employee=request.user, status=status_filter).order_by(
            '-posting_date')

    return render(request, 'leaveHistory.html',
                  {'leave_applications': leave_applications, 'status_filter': status_filter})


@group_required('Admin', 'CEO', 'Manager')
@login_required
def board(request):
    if request.user.is_superuser or request.user.groups.filter(name__in=['Admin']).exists():
        # Superuser and Admin can view all leave applications
        applications = LeaveApplication.objects.all().order_by('-id')
        pending = LeaveApplication.objects.filter(status="Pending").order_by('-posting_date')
        approved = LeaveApplication.objects.filter(status="Approved").order_by('-posting_date')
        rejected = LeaveApplication.objects.filter(status="Rejected").order_by('-posting_date')
        cancelled = LeaveApplication.objects.filter(status="Cancelled").order_by('-posting_date')
    elif request.user.is_CEO or request.user.groups.filter(name='CEO').exists():
        # CEO can only view leave applications submitted by managers
        manager_ids = Account.objects.filter(is_manager=True).values_list('id', flat=True)
        applications = LeaveApplication.objects.filter(employee__id__in=manager_ids).order_by('-id')
        pending = LeaveApplication.objects.filter(employee__id__in=manager_ids, status="Pending").order_by(
            '-posting_date')
        approved = LeaveApplication.objects.filter(employee__id__in=manager_ids, status="Approved").order_by(
            '-posting_date')
        rejected = LeaveApplication.objects.filter(employee__id__in=manager_ids, status="Rejected").order_by(
            '-posting_date')
        cancelled = LeaveApplication.objects.filter(employee__id__in=manager_ids, status="Cancelled").order_by(
            '-posting_date')
    elif request.user.groups.filter(name='Manager').exists():
        # Manager can only view leave applications for their huduma_centre
        if request.user.huduma_centre:  # Check if the Manager has a 'huduma_centre' assigned
            applications = LeaveApplication.objects.filter(employee__huduma_centre=request.user.huduma_centre).order_by(
                '-id')
            # managerapplications = LeaveApplication.objects.filter(employee__huduma_centre=request.user.huduma_centre,
                                                        # employee__is_manager=True).order_by('-posting_date')
            manager_group = Group.objects.get(name="Manager")
            managerapplications = LeaveApplication.objects.filter(employee__groups=manager_group)                                            
            pending = LeaveApplication.objects.filter(employee__huduma_centre=request.user.huduma_centre,
                                                      status="Pending").order_by('-posting_date')
            approved = LeaveApplication.objects.filter(employee__huduma_centre=request.user.huduma_centre,
                                                       status="Approved").order_by('-posting_date')
            rejected = LeaveApplication.objects.filter(employee__huduma_centre=request.user.huduma_centre,
                                                       status="Rejected").order_by('-posting_date')
            cancelled = LeaveApplication.objects.filter(employee__huduma_centre=request.user.huduma_centre,
                                                        status="Cancelled").order_by('-posting_date')
        else:
            # If the manager doesn't have a 'huduma_centre' assigned, handle it appropriately
            return redirect('no_huduma_centre')  # Redirect to an appropriate page or message
    else:
        # Redirect users who are not allowed to view the leave applications
        return redirect('permission_denied')  # Redirect to a permission denied page

    context = {
        "applications": applications,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "cancelled": cancelled,
    }

    return render(request, 'board/index.html', context)


@login_required
def manage_employee(request):
    # Check if the user is a superuser or belongs to the allowed groups
    if request.user.is_superuser or request.user.is_CEO:
        # Superuser (admin) has access to everything
        employees = Account.objects.all().order_by('-id')
    elif request.user.groups.filter(name__in=['Manager', 'CEO', 'Admin']).exists():
        # Check if user is part of the 'Manager', 'CEO', or 'Admin' groups
        if request.user.huduma_centre:  # Ensure the user has a 'huduma_centre' assigned
            employees = Account.objects.filter(huduma_centre=request.user.huduma_centre).order_by('-id')
        else:
            # If the user doesn't have a 'huduma_centre', handle it appropriately
            return redirect('no_huduma_centre')  # Replace with an appropriate page or message
    else:
        # Redirect users who are not allowed
        return redirect('permission_denied')  # You can replace this with your desired page or view

    # Pagination
    paginator = Paginator(employees, 3)  # Show 5 employees per page
    page_no = request.GET.get('page', 1)
    try:
        paginated_employees = paginator.page(page_no)
    except PageNotAnInteger:
        paginated_employees = paginator.page(1)
    except EmptyPage:
        paginated_employees = paginator.page(paginator.num_pages)
    return render(request, 'board/manageEmpl.html', {'employees': paginated_employees})


@login_required
def add_notice(request):
    return render(request, 'board/notice.html')


@login_required
def manage_centres(request):
    if request.method == 'POST':
        huduma_name = request.POST.get('huduma-name')
        location = request.POST.get('location')

        query = HudumaCentre(name=huduma_name, location=location)
        query.save()

    centres = HudumaCentre.objects.all().order_by('created_at')

    return render(request, 'board/centres.html', {'centres': centres})


@group_required('Admin', 'CEO', 'Manager')
@login_required
def manage_leaves(request):
    return render(request, 'board/leaves.html')


def reset_pass(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # print(f"Received email: {email}")  # Debug statement
        if email:
            users = Account.objects.filter(email=email)
            # print(f"Users found: {users.count()}")  # Debug statement
            if users.exists():
                for user in users:
                    uid = urlsafe_base64_encode(force_bytes(user.id))
                    token = default_token_generator.make_token(user)
                    domain = get_current_site(request).domain
                    link = f"http://{domain}/accounts/set_pass/{uid}/{token}/"

                    # Prepare the reset password email
                    email_subject = "Password Reset Request"
                    html_content = render_to_string('reset_email.html', {'link': link})  # Render the HTML template
                    from_email = settings.EMAIL_HOST_USER  # Your configured sender email
                    to_email = [user.email]

                    try:
                        # Create the email object
                        email = EmailMessage(
                            subject=email_subject,
                            body=html_content,
                            from_email=from_email,
                            to=to_email,
                        )

                        # Specify the content type as HTML
                        email.content_subtype = "html"

                        # Send the email
                        email.send(fail_silently=False)
                        messages.success(request, f"Password reset email sent to {user.email}.")
                    except Exception as e:
                        messages.error(request, f"Error sending email to {user.email}: {str(e)}")

                return redirect('login-view')
            else:
                messages.error(request, "No account found with that email address.")
        else:
            messages.error(request, "Please enter a valid email address.")

    return render(request, 'reset-password.html')




@group_required('Admin', 'CEO', 'Manager')
@login_required
def update_leave_application(request, leave_id):
    leave_application = get_object_or_404(LeaveApplication, id=leave_id)
    user = request.user

    if request.method == "POST":
        if leave_application.employee == user and not user.groups.filter(name='CEO').exists():
            messages.error(request, "You cannot approve your own leave application.")
            return redirect('dashboard')

        new_status = request.POST.get('status')
        if new_status == 'Approved' and leave_application.status != 'Approved':
            leave_days = leave_application.no_of_days
            employee = leave_application.employee

            # Deduct the leave days from the user's leave allocation
            if leave_application.leave_type == 'SL':
                if employee.sick_leave_days >= leave_days:
                    employee.sick_leave_days -= leave_days
                else:
                    messages.error(request, "Insufficient sick leave days.")
                    return redirect('dashboard')
            elif leave_application.leave_type == 'CL':
                if employee.casual_leave_days >= leave_days:
                    employee.casual_leave_days -= leave_days
                else:
                    messages.error(request, "Insufficient casual leave days.")
                    return redirect('dashboard')
            elif leave_application.leave_type == 'EL':
                if employee.emergency_leave_days >= leave_days:
                    employee.emergency_leave_days -= leave_days
                else:
                    messages.error(request, "Insufficient emergency leave days.")
                    return redirect('dashboard')

            employee.save()

        leave_application.status = new_status
        leave_application.admin_remarks = request.POST.get('admin_remarks')
        leave_application.save()
        messages.success(request, "Leave application updated successfully!")
        return redirect('dashboard')  # Replace with your dashboard view name
    else:
        messages.error(request, "Invalid request.")
        return redirect('dashboard')



def permission_denied(request):
    return render(request, 'permission_denied.html')





def set_pass(request, uid, token):
    try:
        # Decode the user ID and retrieve the user
        user_id = urlsafe_base64_decode(uid).decode('utf-8')
        user = get_user_model().objects.get(id=user_id)

        # Check the token
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')
                if new_password and new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()

                    # Send email notification
                    email_subject = "Password Changed Successfully"
                    html_content = render_to_string('confirm_pass.html', {'user': user})
                    from_email = settings.EMAIL_HOST_USER
                    to_email = [user.email]

                    try:
                        email = EmailMessage(
                            subject=email_subject,
                            body=html_content,
                            from_email=from_email,
                            to=to_email,
                        )
                        email.content_subtype = "html"
                        email.send(fail_silently=False)
                    except Exception as e:
                        # Log or display the exception message
                        messages.error(request, f"Error sending email: {str(e)}")

                    messages.success(request, "Your password has been successfully updated!")
                    return redirect('login-view')
                else:
                    messages.error(request, "Passwords do not match or are invalid.")
            return render(request, 'set-password.html', {'uid': uid, 'token': token})
        else:
            messages.error(request, "The password reset link is invalid or has expired.")
            return redirect('login-view')
    except ObjectDoesNotExist :
        # Specific exception for user not found
        messages.error(request, "User not found.")
        return redirect('login-view')
    except ValueError:
        # If URL decoding fails
        messages.error(request, "Invalid reset link.")
        return redirect('login-view')
    except Exception as e:
        # Log the general exception for unexpected errors
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('login-view')



