def build_email_verification_html(
    full_name: str,
    verification_link: str,
) -> tuple[str, str]:
    return (
        "ASRP registration - email verification",
        f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {full_name},</p>

    <p>
        Thank you for creating an account with the American Society of
        Russian-Speaking Pathologists (ASRP).
    </p>

    <p>
        To complete your registration, please verify your email address by
        clicking the link below:
    </p>

    <p>
        <a href="{verification_link}"
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
        <a href="{reset_link}"
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
