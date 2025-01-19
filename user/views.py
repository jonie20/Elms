from datetime import datetime, timedelta
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.views import View
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from user.authentication import AccountAuthentication

from user.models import Account, LeaveApplication, HudumaCentre


class RegisterView(View):
    def get(self, request):
        # Render the form with all available Huduma Centres
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


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login-view')


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
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        description = request.POST.get('description')

        if LeaveApplication.objects.filter(employee=request.user, status='Pending').exists():
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
            employee=request.user,
        )

        # Calculate the number of working days (excluding weekends and holidays)
        leave_application.no_of_days = leave_application.calculate_working_days()

        if leave_application.no_of_days > request.user.total_leave_days:
            messages.error(request, "You do not have enough leave days available.")
            return redirect('apply_leave')

        leave_application.save()

        messages.success(request, "Leave application submitted successfully.")
        return redirect('dash')  # Redirect to user's dashboard or any relevant page

    return render(request, 'apply_leave.html')
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


@login_required
def board(request):
    applications = LeaveApplication.objects.all().order_by('-id')
    pending = LeaveApplication.objects.filter(status="Pending").order_by('-posting_date')
    approved = LeaveApplication.objects.filter(status="Approved").order_by('-posting_date')
    rejected = LeaveApplication.objects.filter(status="Rejected").order_by('-posting_date')
    cancelled = LeaveApplication.objects.filter(status="Cancelled").order_by('-posting_date')

    context = {
        "applications": applications,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "cancelled": cancelled,
    }

    return render(request, 'board/index.html', context)


@login_required
def add_employee(request):
    if request.method == 'POST':
        personal_number = request.POST.get('EmplId')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        # date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('from_date')
        department = request.POST.get('from_date')

        query = Account(first_name=first_name, last_name=last_name, email=email, phone_number=phone_number,
                        personal_number=personal_number, gender=gender, department=department)
        query.save()

    return render(request, 'board/employee.html')


@login_required
def manage_employee(request):
    Employees = Account.objects.all().order_by('-id')
    # context = {
    #     'Employees' : Employees
    # }

    return render(request, 'board/manageEmpl.html', {'Employees': Employees})


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


@login_required
def manage_leaves(request):
    return render(request, 'board/leaves.html')


def set_pass(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            users = Account.objects.filter(email=email)
            for user in users:
                uid = urlsafe_base64_encode(force_bytes(user.id))
                token = default_token_generator.make_token(user)
                domain = get_current_site(request).domain
                link = f"http://{domain}/reset/{uid}/{token}/"

                # Prepare the reset password email
                email_subject = "Password Reset Request"
                email_message = render_to_string(
                    'reset_email.html', {'link': link}
                )
                from_email = settings.EMAIL_HOST_USER  # Your configured sender email
                to_email = [user.email]
                # send_mail(email_subject,email_message, [settings.EMAIL_HOST_USER], [user.email],fail_silently=False)
                send_mail(
                    email_subject,
                    email_message,
                    from_email,  # Sender email
                    to_email,    # List of recipients
                    fail_silently=False
                )

            return redirect('password_reset_done')
    return render(request, 'reset-password.html')


    return render(request, 'reset-password.html')




def update_leave_application(request, id):
    leave_application = get_object_or_404(LeaveApplication, id=id)
    if request.method == "POST":
        print(leave_application.id)
        leave_application.status = request.POST.get('status')
        leave_application.admin_remarks = request.POST.get('admin_remarks')
        leave_application.save()
        messages.success(request, "Leave application updated successfully!")
        return redirect('dashboard')  # Replace with your dashboard view name
    else:
        messages.error(request, "Invalid request.")
        return redirect('dashboard')
