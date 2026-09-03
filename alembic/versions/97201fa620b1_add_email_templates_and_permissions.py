"""add_email_templates_and_permissions

Revision ID: 97201fa620b1
Revises: d5e8f31a4b72
Create Date: 2026-07-17 09:31:01.530560

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.core.config import DEV_MODE


revision: str = '97201fa620b1'
down_revision: Union[str, None] = 'd5e8f31a4b72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EMAIL_VERIFICATION_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {{ user.firstname }} {{ user.lastname }},</p>

    <p>
        Thank you for creating an account with the American Society of
        Russian-Speaking Pathologists (ASRP).
    </p>

    <p>
        To complete your registration, please verify your email address by
        clicking the link below:
    </p>

    <p>
        <a href="{{ verification_link }}"
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
"""


PASSWORD_RESET_HTML = """
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
        <a href="{{ reset_link }}"
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
"""


MEMBERSHIP_APPLICATION_RECEIVED_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {{ user.firstname }} {{ user.lastname }},</p>

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
"""


MEMBERSHIP_APPLICATION_APPROVED_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {{ user.firstname }} {{ user.lastname }},</p>

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
        <a
            href="{{ login_link }}"
               style="
               display: inline-block;
               padding: 12px 20px;
               background-color: #2563eb;
               color: #ffffff;
               text-decoration: none;
               border-radius: 6px;
               font-weight: bold;
            ">
            Login Link
        </a>
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
"""


MEMBERSHIP_APPLICATION_REJECTED_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {{ user.firstname }} {{ user.lastname }},</p>

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
"""


MEMBERSHIP_SUSPENDED_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {{ user.firstname }} {{ user.lastname }},</p>

    <p>
        This email serves as formal notice that your ASRP membership and account
        access have been temporarily suspended due to a violation of the ASRP
        Code of Conduct and/or Community Guidelines.
    </p>

    <p>
        <strong>Reason for Suspension:</strong> {{ reason }}
    </p>

    <p>
        During the suspension period, you will not have access to member-only
        resources, discussion forums, events, or other membership benefits. You
        may submit an appeal by contacting admin@asrpath.org. If the suspension
        is lifted, your membership privileges may be restored, provided no
        additional violations occur and any applicable conditions have been
        satisfied.
    </p>

    <p>
        ASRP is committed to maintaining a professional, respectful, and
        inclusive environment for all members.
    </p>

    <p>
        Sincerely,<br>
        Board of Directors<br>
        American Society of Russian-Speaking Pathologists
    </p>
</body>
</html>
"""


MEMBERSHIP_TERMINATED_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
    <p>Dear {{ user.firstname }} {{ user.lastname }},</p>

    <p>
        This email serves as formal notice that your membership in the American
        Society of Russian-Speaking Pathologists (ASRP) has been terminated
        following a review of conduct that was determined to violate the ASRP
        Code of Conduct and/or Community Guidelines.
    </p>

    <p>
        <strong>Reason for Termination:</strong> {{ reason }}
    </p>

    <p>
        Effective immediately, your membership status has been revoked and your
        account access has been permanently disabled. You will no longer be
        eligible to participate in ASRP member activities, access member-only
        resources, or represent yourself as an active member of ASRP.
    </p>

    <p>
        If you believe this action was taken in error, you may submit an appeal
        by contacting admin@asrpath.org within 30 days of receiving this notice.
        Any appeal will be reviewed by the appropriate ASRP leadership body, and
        its decision will be final.
    </p>

    <p>
        ASRP remains committed to fostering a professional, respectful, and
        supportive community for all members.
    </p>

    <p>
        Sincerely,<br>
        Board of Directors<br>
        American Society of Russian-Speaking Pathologists
    </p>
</body>
</html>
"""


def upgrade() -> None:
    op.create_table('email_templates',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('subject', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.Column(
        'template_type',
        sa.Enum(
            'CUSTOM',
            'EMAIL_VERIFICATION',
            'PASSWORD_RESET',
            'MEMBERSHIP_RENEWAL',
            'MEMBERSHIP_APPLICATION_RECEIVED',
            'MEMBERSHIP_APPLICATION_APPROVED',
            'MEMBERSHIP_APPLICATION_REJECTED',
            'MEMBERSHIP_SUSPENDED',
            'MEMBERSHIP_TERMINATED',
            name='email_template_type_enum',
        ),
        nullable=False,
    ),
    sa.Column('editor_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('html', sa.String(), nullable=False),
    sa.Column('_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_email_templates_created_by_id_users')),
    sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], name=op.f('fk_email_templates_updated_by_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_email_templates'))
    )

    metadata = sa.MetaData()
    bind = op.get_bind()
    email_templates_table = sa.Table("email_templates", metadata, autoload_with=bind)
    permissions_table = sa.Table("permissions", metadata, autoload_with=bind)

    default_email_templates = [
        {
            "name": "Email verification",
            "subject": "ASRP registration - email verification",
            "description": "Sent to user to verify their email address during registration.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "EMAIL_VERIFICATION",
            "editor_state": {},
            "html": EMAIL_VERIFICATION_HTML,
        },
        {
            "name": "Password reset",
            "subject": "ASRP password reset",
            "description": "Sent to users who requested a password reset.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "PASSWORD_RESET",
            "editor_state": {},
            "html": PASSWORD_RESET_HTML,
        },
        {
            "name": "Membership renewal",
            "subject": "ASRP membership renewal",
            "description": "Sent to user as a reminder that their subscription will soon expire.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "MEMBERSHIP_RENEWAL",
            "editor_state": {},
            "html": "",
        },
        {
            "name": "Membership application received",
            "subject": "ASRP membership application received",
            "description": "Sent after a paid membership application is received.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "MEMBERSHIP_APPLICATION_RECEIVED",
            "editor_state": {},
            "html": MEMBERSHIP_APPLICATION_RECEIVED_HTML,
        },
        {
            "name": "Membership application approved",
            "subject": "Your ASRP membership application has been approved",
            "description": "Sent when a membership application is approved.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "MEMBERSHIP_APPLICATION_APPROVED",
            "editor_state": {},
            "html": MEMBERSHIP_APPLICATION_APPROVED_HTML,
        },
        {
            "name": "Membership application rejected",
            "subject": "Your ASRP membership application has been rejected",
            "description": "Sent when a membership application is rejected.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "MEMBERSHIP_APPLICATION_REJECTED",
            "editor_state": {},
            "html": MEMBERSHIP_APPLICATION_REJECTED_HTML,
        },
        {
            "name": "Membership suspended",
            "subject": "Your ASRP membership suspended",
            "description": "Sent when a membership is temporarily suspended.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "MEMBERSHIP_SUSPENDED",
            "editor_state": {},
            "html": MEMBERSHIP_SUSPENDED_HTML,
        },
        {
            "name": "Membership terminated",
            "subject": "Your ASRP membership terminated",
            "description": "Sent when a membership is terminated.",
            "created_by_id": None,
            "updated_by_id": None,
            "template_type": "MEMBERSHIP_TERMINATED",
            "editor_state": {},
            "html": MEMBERSHIP_TERMINATED_HTML,
        },
    ]
    op.bulk_insert(email_templates_table, default_email_templates)

    new_permissions = [
        {"action": "email_templates.create", "name": "Create email templates"},
        {"action": "email_templates.view", "name": "View email templates"},
        {"action": "email_templates.delete", "name": "Remove email templates"},
        {"action": "email_templates.update", "name": "Update email templates"},
    ]
    op.bulk_insert(permissions_table, new_permissions)

    if DEV_MODE:
        op.execute(
            "INSERT INTO users_permissions (permission_id, user_id) "
            "SELECT id, 1 FROM permissions WHERE action IN "
            "('email_templates.create', 'email_templates.view', 'email_templates.delete', 'email_templates.update')"
        )


def downgrade() -> None:
    op.drop_table('email_templates')
    op.execute("DROP TYPE IF EXISTS email_template_type_enum")

    op.execute(
        "DELETE FROM users_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE action IN "
        "('email_templates.create', 'email_templates.view', 'email_templates.delete', 'email_templates.update'))"
    )
    op.execute("DELETE FROM permissions WHERE action IN ('email_templates.create', 'email_templates.view', 'email_templates.delete', 'email_templates.update')")
