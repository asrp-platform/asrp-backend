from html import escape


def build_email_verification_html(
    full_name: str,
    verification_link: str,
) -> tuple[str, str]:
    safe_full_name = escape(full_name)
    safe_verification_link = escape(verification_link, quote=True)

    return (
        "ASRP registration - email verification",
        f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {safe_full_name},</p>

    <p>
        Thank you for creating an account with the American Society of
        Russian-Speaking Pathologists (ASRP).
    </p>

    <p>
        To complete your registration, please verify your email address by
        clicking the link below:
    </p>

    <p>
        <a href="{safe_verification_link}"
           style="
               display: inline-block;
               padding: 12px 20px;
               background-color: #2563eb;
               color: #ffffff;
               text-decoration: none;
               border-radius: 6px;
               font-weight: bold;
           ">
            Verify Email Address
        </a>
    </p>

    <p>
        If you did not create an account with ASRP, you may safely ignore this email.
    </p>

    <p>
        We look forward to welcoming you to our growing community of
        Russian-speaking pathologists and pathology trainees.
    </p>

    <p>
        Best regards,<br>
        Board of Directors<br>
        American Society of Russian-Speaking Pathologists
    </p>
</body>
</html>
""",
    )


def build_password_reset_html(
    reset_link: str,
) -> tuple[str, str]:
    safe_reset_link = escape(reset_link, quote=True)

    return (
        "ASRP password reset",
        f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">

    <p>
        We received a request to reset the password for your account with the
        American Society of Russian-Speaking Pathologists (ASRP).
    </p>

    <p>
        To set a new password, please click the button below:
    </p>

    <p>
        <a href="{safe_reset_link}"
           style="
               display: inline-block;
               padding: 12px 20px;
               background-color: #2563eb;
               color: #ffffff;
               text-decoration: none;
               border-radius: 6px;
               font-weight: bold;
           ">
            Reset Password
        </a>
    </p>

    <p>
        This password reset link is valid for 1 hour.
    </p>

    <p>
        If you did not request a password reset, you may safely ignore this email.
        Your password will remain unchanged.
    </p>

    <p>
        Best regards,<br>
        Board of Directors<br>
        American Society of Russian-Speaking Pathologists
    </p>

</body>
</html>
""",
    )


def build_membership_application_html(
    full_name: str,
) -> tuple[str, str]:
    safe_full_name = escape(full_name)

    return (
        "ASRP membership application received",
        f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {safe_full_name},</p>

    <p>
        Thank you for applying for membership in the American Society of
        Russian-Speaking Pathologists (ASRP).
    </p>

    <p>
        We have successfully received your application and our Membership
        Committee is currently reviewing your submission. This process may take
        several business days.
    </p>

    <p>
        You will receive a separate email once a decision has been made
        regarding your application.
    </p>

    <p>
        We appreciate your interest in joining ASRP and contributing to our
        professional community.
    </p>

    <p>
        Best regards,<br>
        Board of Directors<br>
        American Society of Russian-Speaking Pathologists
    </p>
</body>
</html>
""",
    )


def build_membership_application_approved_html(
    full_name: str,
    login_link: str,
) -> tuple[str, str]:
    safe_full_name = escape(full_name)
    safe_login_link = escape(login_link, quote=True)

    return (
        "Your ASRP membership application has been approved",
        f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {safe_full_name},</p>

    <p>
        Congratulations! Your membership application has been approved.
    </p>

    <p>
        We are delighted to welcome you to the American Society of
        Russian-Speaking Pathologists (ASRP).
    </p>

    <p>
        As a member, you now have access to our community, educational
        resources, networking opportunities, mentorship initiatives, and future
        society events.
    </p>

    <p>
        You may log in to your account here:
        <a href="{safe_login_link}">Login Link</a>
    </p>

    <p>
        Thank you for joining ASRP. We look forward to your participation and
        contributions to our community.
    </p>

    <p>
        Welcome aboard!
    </p>

    <p>
        Best regards,<br>
        Board of Directors<br>
        American Society of Russian-Speaking Pathologists
    </p>
</body>
</html>
""",
    )


def build_membership_application_rejected_html(
    full_name: str,
) -> tuple[str, str]:
    safe_full_name = escape(full_name)

    return (
        "Your ASRP membership application status",
        f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {safe_full_name},</p>

    <p>
        Thank you for your interest in the American Society of Russian-Speaking
        Pathologists (ASRP).
    </p>

    <p>
        After careful review, we are unable to approve your membership
        application at this time.
    </p>

    <p>
        This decision may be based on membership eligibility requirements or
        incomplete application information.
    </p>

    <p>
        If you believe additional information may be helpful, or if you have
        questions regarding this decision, please contact us at
        admin@asrpath.org.
    </p>

    <p>
        We appreciate your interest in ASRP and wish you success in your
        professional endeavors.
    </p>

    <p>
        Best regards,<br>
        Board of Directors<br>
        American Society of Russian-Speaking Pathologists
    </p>
</body>
</html>
""",
    )
