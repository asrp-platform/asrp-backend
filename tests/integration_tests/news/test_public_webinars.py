from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.domains.news.services import has_member_access, serialize_user_webinar


def make_webinar(*, member_only: bool):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=1,
        created_at=now,
        updated_at=now,
        title="Test webinar",
        description="Description",
        learning_objectives=[],
        slug="test-webinar",
        speaker_name="Test Speaker",
        speaker_description=None,
        registration_link="https://example.com/register",
        join_link="https://example.com/join",
        recording_link="https://example.com/recording",
        starts_at=now,
        location="Online",
        member_only=member_only,
        registered_users=[],
    )


def test_guest_cannot_view_links():
    response = serialize_user_webinar(
        make_webinar(member_only=False),
        user_id=None,
        membership=None,
    )

    assert response.registration_link is None
    assert response.join_link is None
    assert response.recording_link is None


def test_authenticated_non_member_can_view_public_webinar_links():
    response = serialize_user_webinar(
        make_webinar(member_only=False),
        user_id=1,
        membership=None,
    )

    assert str(response.join_link) == "https://example.com/join"


def test_authenticated_non_member_cannot_view_member_only_links():
    response = serialize_user_webinar(
        make_webinar(member_only=True),
        user_id=1,
        membership=None,
    )

    assert response.registration_link is None
    assert response.join_link is None
    assert response.recording_link is None


def test_active_member_can_view_member_only_links():
    response = serialize_user_webinar(
        make_webinar(member_only=True),
        user_id=1,
        membership=SimpleNamespace(is_active=True, terminated=False, is_suspended=False),
    )

    assert str(response.registration_link) == "https://example.com/register"
    assert str(response.join_link) == "https://example.com/join"
    assert str(response.recording_link) == "https://example.com/recording"


def test_membership_access_requires_active_unsuspended_membership():
    membership = SimpleNamespace(
        is_active=True,
        terminated=False,
        is_suspended=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    assert has_member_access(membership) is True

    membership.is_suspended = True
    assert has_member_access(membership) is False


def test_registration_indicator_matches_current_user():
    webinar = make_webinar(member_only=False)
    webinar.registered_users = [SimpleNamespace(id=1)]

    assert serialize_user_webinar(webinar, user_id=1, membership=None).is_registered is True
    assert serialize_user_webinar(webinar, user_id=2, membership=None).is_registered is False
    assert serialize_user_webinar(webinar, user_id=None, membership=None).is_registered is False
