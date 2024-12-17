from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from user.authentication import AccountAuthentication
from user.models import Account, LeaveApplication


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        account_model = Account.objects.create(
            first_name=request.POST['first-name'],
            last_name=request.POST['last-name'],
            username=request.POST['username'],
            email=request.POST['email'],
        )
        account_model.set_password(request.POST['password1'])
        account_model.save()
        user = AccountAuthentication.authenticate(request, email=request.POST['email'],
                                                  password=request.POST['password1'])
        login(request, user)
        return redirect('dash')


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
            if user.is_superuser or user.is_admin:  # For admin users
                return redirect('/account/board')
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

        total_days = (to_date_obj - from_date_obj).days + 1

        if total_days > request.user.total_leave_days:
            messages.error(request, "You do not have enough leave days available.")
            return redirect('apply_leave')

        leave_application = LeaveApplication(
            leave_type=leave_type,
            from_date=from_date_obj,
            to_date=to_date_obj,
            description=description,
            employee=request.user,

        )
        leave_application.save()
        messages.success(request, "Leave application submitted successfully.")
        return redirect('dash')

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


def board(request):
    applications = LeaveApplication.objects.filter(employee=request.user).order_by('-id')

    return render(request, 'board/index.html', {'applications': applications})


def add_employee(request):
    if request.method == 'POST':
        personal_number= request.POST.get('EmplId')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('first_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        # date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('from_date')
        designation = request.POST.get('designation')
        profile_picture= request.POST.get('profile_picture')

        query = Account(first_name=first_name, last_name=last_name, email=email,
                        phone_number=phone_number,personal_number=personal_number,gender=gender,
                        designation=designation,profile_picture=profile_picture)
        query.save()
        user = AccountAuthentication.authenticate(request, email=request.POST['email'],
                                                  password=request.POST['password1'])
        login(request, user)

    return render(request, 'board/employee.html')


def manage_employee(request):
    Employees = Account.objects.all().order_by('-id')
    # context = {
    #     'Employees' : Employees
    # }

    return render(request, 'board/manageEmpl.html', {'Employees': Employees})


def add_notice(request):
    # leave_applications = LeaveApplication.objects.all()
    # context = {
    #         'leave_applications': leave_applications,
    # }

    return render(request, 'board/notice.html')
