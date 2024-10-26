from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from .models import Notification


# logger = logging.getLogger(__name__)

def send_email(subject, message, recipient_list):
    """
    Send an email using configured SMTP settings.
    """
    try:
        # Directly send the email using Django's send_mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        print(f"Email sent successfully to {', '.join(recipient_list)}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def log_and_send_email(user, action_type, ip_address=None, **kwargs):
    """
    Log the notification and send an email based on the action type.
    """
    notification = Notification.objects.create(user=user, action_type=action_type)

    email_functions = {
        'SIGNUP': send_signup_email,
        'LOGIN': lambda user: send_login_email(user, ip_address),
        'KYC_CONFIRMED': send_kyc_confirmation_email,
        'PASSWORD_RESET': lambda user: send_password_reset_email(user, kwargs.get('reset_url')),
        'PAYMENT_SUCCESSFUL': send_payment_successful_email,
        'PAYMENT_FAILED': send_payment_failed_email,
        'CONTRIBUTION_SUCCESSFUL': lambda user: send_contribution_email(user, **kwargs),
        'CYCLE_PAYMENT_RECEIVED': lambda user: send_cycle_payment_email(user, **kwargs),
        'FAILED_PAYMENT': lambda user: send_failed_payment_alert(user, **kwargs),
        'WALLET_WITHDRAWAL': lambda user: send_wallet_withdrawal_email(user, **kwargs),
        'WALLET_DEPOSIT': lambda user: send_wallet_deposit_email(user, **kwargs),
        'GROUP_JOIN': lambda user: send_group_join_email(user, **kwargs),
        'GROUP_REMOVAL': lambda user: send_group_removal_email(user, **kwargs),
        'GROUP_INVITATION': lambda user: send_group_invitation_email(user, **kwargs),
    }
    
    email_function = email_functions.get(action_type)
    
    if email_function:
        success = email_function(user)
        notification.email_sent = success
        notification.save()
    else:
        print(f"Unknown action type: {action_type}")

def send_contribution_email(user, amount=None, group_name=None):
    subject = "Contribution Successfully Made"
    message = f"""
    Hi {user.username},

    Your contribution of {amount} has been successfully processed for the group '{group_name}'.

    Thank you for your participation!

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_cycle_payment_email(user, amount=None, cycle_number=None):
    subject = "Cycle Payment Received"
    message = f"""
    Hi {user.username},

    Great news! You have received a cycle payment of {amount} for cycle #{cycle_number}.

    The amount has been credited to your account.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_failed_payment_alert(user, amount=None, reason=None):
    subject = "Payment Failed Alert"
    message = f"""
    Hi {user.username},

    We noticed that a payment of {amount} has failed.
    Reason: {reason}

    Please ensure you have sufficient funds and try again.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_wallet_withdrawal_email(user, amount=None, transaction_id=None):
    subject = "Wallet Withdrawal Successful"
    message = f"""
    Hi {user.username},

    Your wallet withdrawal of {amount} has been successfully processed.
    Transaction ID: {transaction_id}

    The funds should reflect in your account shortly.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_wallet_deposit_email(user, amount=None, transaction_id=None):
    subject = "Wallet Deposit Successful"
    message = f"""
    Hi {user.username},

    Your wallet has been successfully credited with {amount}.
    Transaction ID: {transaction_id}

    The funds are now available in your account.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_group_join_email(user, group_name=None):
    subject = "Welcome to the Group"
    message = f"""
    Hi {user.username},

    You have successfully joined the group '{group_name}'.

    You can now participate in group activities and view group details.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_group_removal_email(user, group_name=None, reason=None):
    subject = "Group Removal Notice"
    message = f"""
    Hi {user.username},

    You have been removed from the group '{group_name}'.
    Reason: {reason}

    If you believe this was done in error, please contact our support team.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_group_invitation_email(user, group_name=None, inviter=None):
    subject = "New Group Invitation"
    message = f"""
    Hi {user.username},

    You have been invited to join the group '{group_name}' by {inviter}.

    To accept or decline this invitation, please log in to your account.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_signup_email(user):
    subject = "Welcome to Thrifto!"
    message = f"""
    Hi {user.username},

    Welcome to our Thrifto! Your account has been successfully created.

    Get started by completing your profile and exploring our features.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_login_email(user, ip_address):
    subject = "New Login Detected"
    message = f"""
    Hi {user.username},

    We detected a new login to your account. If this was you, no further action is needed.

    Email: {user.email}
    IP Address: {ip_address}

    If you didn't log in recently, please contact our support team immediately.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_kyc_confirmation_email(user):
    """
    Send KYC confirmation email.
    """
    subject = "KYC Verification Successful"
    message = f"""
    Hi {user.username},

    Great news! Your KYC (Know Your Customer) verification has been successfully completed.

    You now have full access to all our platform features.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_payment_successful_email(user):
    subject = "Payment Successful"
    message = f"""
    Hi {user.username},

    We're writing to confirm that your recent payment was successful.

    Thank you for your business!

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def send_payment_failed_email(user):
    subject = "Payment Failed"
    message = f"""
    Hi {user.username},

    We regret to inform you that your recent payment attempt was unsuccessful.

    Please check your payment details and try again. If you continue to experience issues, please contact our support team.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])

def get_client_ip(request):
    """
    Get the client's IP address from the request.
    This handles situations where the app is behind a proxy.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_password_reset_email(user, reset_url):
    subject = "Password Reset Request"
    message = f"""
    Hi {user.username},

    You recently requested to reset your password. Please click the link below to reset it:

    {reset_url}

    This link will expire in 5 minutes for security reasons.
    If you didn't request this, please ignore this email or contact support if you have concerns.

    Best regards,
    The Team
    """
    return send_email(subject, message, [user.email])