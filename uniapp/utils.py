import random
from django.core.mail import send_mail
from django.utils.timezone import now
from .models import OTPVerification
from .models import Student, Faculty, Admin, Department

def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_otp(email):
    """Generate and send OTP to the user."""
    otp_code = generate_otp()

    # Store OTP (overwrite if exists)
    OTPVerification.objects.update_or_create(email=email, defaults={"otp": otp_code, "created_at": now()})

    # Send OTP via email
    send_mail(
        subject="Your UniPulse Login OTP",
        message=f"Your OTP is: {otp_code}. It expires in 15 minutes.",
        from_email="your-email@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )

from django.core.exceptions import ObjectDoesNotExist
 
from rest_framework.exceptions import ValidationError, NotFound



from rest_framework.exceptions import ValidationError, NotFound

def get_user_by_type_and_details(user_type, email, enrollment_number=None, department_name=None):
    if user_type == "student":
        user = Student.objects.filter(email=email, enrollment_number=enrollment_number).first()
        if not user:
            raise NotFound("Student not found with provided email and enrollment number.")
        return user

    elif user_type == "faculty":
        if not department_name:
            raise ValidationError("Department is required for faculty.")
        
        # Get the department instance
        try:
            dept = Department.objects.get(name__iexact=department_name)
        except Department.DoesNotExist:
            raise ValidationError("Invalid department name.")

        user = Faculty.objects.filter(email=email, department=dept).first()
        if not user:
            raise ValidationError("Faculty with this email is not associated with the specified department.")
        return user

    elif user_type == "admin":
        if not department_name:
            raise ValidationError("Department is required for admin.")

        try:
            dept = Department.objects.get(name__iexact=department_name)
        except Department.DoesNotExist:
            raise ValidationError("Invalid department name.")

        user = Admin.objects.filter(email=email, department=dept).first()
        if not user:
            raise ValidationError("Admin with this email is not associated with the specified department.")
        return user

    else:
        raise ValidationError("Invalid user type.")
