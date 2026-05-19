"""
Tests for app.core.guardian — the permission layer.
All pure-Python; no database required.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.core.guardian import Guardian, PermissionDenied, get_guardian
from tests.conftest import _FakeUser, _FakeTopic, _FakePost, _FakeCategory


# ── Helpers ──────────────────────────────────────────────────────────────────


def _future(days: int = 1):
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days)


def _past(days: int = 1):
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)


# ── Identity properties ───────────────────────────────────────────────────────


class TestIdentity:
    def test_anon_is_not_authenticated(self):
        g = Guardian(None)
        assert not g.is_authenticated

    def test_user_is_authenticated(self, regular_user):
        assert Guardian(regular_user).is_authenticated

    def test_anon_is_not_admin(self):
        assert not Guardian(None).is_admin

    def test_admin_flag(self, admin_user):
        assert Guardian(admin_user).is_admin

    def test_regular_user_is_not_admin(self, regular_user):
        assert not Guardian(regular_user).is_admin

    def test_mod_flag(self, mod_user):
        assert Guardian(mod_user).is_moderator

    def test_admin_is_staff(self, admin_user):
        assert Guardian(admin_user).is_staff

    def test_mod_is_staff(self, mod_user):
        assert Guardian(mod_user).is_staff

    def test_regular_is_not_staff(self, regular_user):
        assert not Guardian(regular_user).is_staff

    def test_anon_is_not_silenced(self):
        assert not Guardian(None).is_silenced

    def test_user_silenced_in_future(self, regular_user):
        regular_user.silenced_till = _future()
        assert Guardian(regular_user).is_silenced

    def test_user_silence_expired(self, regular_user):
        regular_user.silenced_till = _past()
        assert not Guardian(regular_user).is_silenced

    def test_no_silenced_till_attr(self, regular_user):
        del regular_user.silenced_till
        # getattr fallback → None
        assert not Guardian(regular_user).is_silenced

    def test_anon_is_not_suspended(self):
        assert not Guardian(None).is_suspended

    def test_user_suspended_in_future(self, regular_user):
        regular_user.suspended_till = _future()
        assert Guardian(regular_user).is_suspended

    def test_user_suspension_expired(self, regular_user):
        regular_user.suspended_till = _past()
        assert not Guardian(regular_user).is_suspended


# ── Category permissions ──────────────────────────────────────────────────────


class TestCategoryPermissions:
    def test_open_category_visible_to_anon(self, open_category):
        assert Guardian(None).can_see_category(open_category)

    def test_restricted_category_hidden_from_anon(self, restricted_category):
        assert not Guardian(None).can_see_category(restricted_category)

    def test_restricted_category_visible_to_staff(self, admin_user, restricted_category):
        assert Guardian(admin_user).can_see_category(restricted_category)

    def test_restricted_category_visible_to_mod(self, mod_user, restricted_category):
        assert Guardian(mod_user).can_see_category(restricted_category)


# ── Topic permissions ─────────────────────────────────────────────────────────


class TestTopicPermissions:
    def test_can_see_normal_topic(self, regular_user, open_topic):
        assert Guardian(regular_user).can_see_topic(open_topic)

    def test_anon_cannot_see_deleted_topic(self, deleted_topic):
        assert not Guardian(None).can_see_topic(deleted_topic)

    def test_staff_can_see_deleted_topic(self, admin_user, deleted_topic):
        assert Guardian(admin_user).can_see_topic(deleted_topic)

    def test_invisible_topic_hidden_from_anon(self):
        topic = _FakeTopic(visible=False)
        assert not Guardian(None).can_see_topic(topic)

    def test_invisible_topic_visible_to_staff(self, admin_user):
        topic = _FakeTopic(visible=False)
        assert Guardian(admin_user).can_see_topic(topic)

    def test_topic_in_restricted_category_hidden(self, regular_user, open_topic, restricted_category):
        assert not Guardian(regular_user).can_see_topic(open_topic, restricted_category)

    def test_topic_in_restricted_category_staff_ok(self, admin_user, open_topic, restricted_category):
        assert Guardian(admin_user).can_see_topic(open_topic, restricted_category)

    def test_anon_cannot_create_topic(self, open_category):
        assert not Guardian(None).can_create_topic(open_category)

    def test_regular_can_create_topic(self, regular_user, open_category):
        assert Guardian(regular_user).can_create_topic(open_category)

    def test_silenced_user_cannot_create_topic(self, regular_user):
        regular_user.silenced_till = _future()
        assert not Guardian(regular_user).can_create_topic()

    def test_suspended_user_cannot_create_topic(self, regular_user):
        regular_user.suspended_till = _future()
        assert not Guardian(regular_user).can_create_topic()

    def test_cannot_create_in_restricted_category(self, regular_user, restricted_category):
        assert not Guardian(regular_user).can_create_topic(restricted_category)

    def test_can_edit_own_topic(self, regular_user, open_topic):
        open_topic.user_id = regular_user.id
        assert Guardian(regular_user).can_edit_topic(open_topic)

    def test_cannot_edit_others_topic(self, regular_user, open_topic, other_user):
        open_topic.user_id = other_user.id
        assert not Guardian(regular_user).can_edit_topic(open_topic)

    def test_staff_can_edit_any_topic(self, admin_user, open_topic, other_user):
        open_topic.user_id = other_user.id
        assert Guardian(admin_user).can_edit_topic(open_topic)

    def test_cannot_edit_deleted_own_topic(self, regular_user, deleted_topic):
        deleted_topic.user_id = regular_user.id
        assert not Guardian(regular_user).can_edit_topic(deleted_topic)

    def test_can_delete_own_topic(self, regular_user, open_topic):
        open_topic.user_id = regular_user.id
        assert Guardian(regular_user).can_delete_topic(open_topic)

    def test_cannot_delete_others_topic(self, regular_user, open_topic, other_user):
        open_topic.user_id = other_user.id
        assert not Guardian(regular_user).can_delete_topic(open_topic)


# ── Post permissions ──────────────────────────────────────────────────────────


class TestPostPermissions:
    def test_anon_cannot_create_post(self, open_topic):
        assert not Guardian(None).can_create_post(open_topic)

    def test_regular_can_create_post(self, regular_user, open_topic):
        assert Guardian(regular_user).can_create_post(open_topic)

    def test_cannot_post_in_closed_topic(self, regular_user, closed_topic):
        assert not Guardian(regular_user).can_create_post(closed_topic)

    def test_staff_can_post_in_closed_topic(self, admin_user, closed_topic):
        assert Guardian(admin_user).can_create_post(closed_topic)

    def test_silenced_cannot_post(self, regular_user, open_topic):
        regular_user.silenced_till = _future()
        assert not Guardian(regular_user).can_create_post(open_topic)

    def test_cannot_post_in_deleted_topic(self, regular_user, deleted_topic):
        assert not Guardian(regular_user).can_create_post(deleted_topic)

    def test_archived_topic_blocks_post(self, regular_user):
        topic = _FakeTopic(archived=True)
        assert not Guardian(regular_user).can_create_post(topic)

    def test_can_edit_own_post(self, regular_user, open_post):
        open_post.user_id = regular_user.id
        assert Guardian(regular_user).can_edit_post(open_post)

    def test_cannot_edit_others_post(self, regular_user, open_post, other_user):
        open_post.user_id = other_user.id
        assert not Guardian(regular_user).can_edit_post(open_post)

    def test_staff_can_edit_any_post(self, admin_user, open_post, other_user):
        open_post.user_id = other_user.id
        assert Guardian(admin_user).can_edit_post(open_post)

    def test_cannot_edit_deleted_post(self, regular_user, deleted_post):
        deleted_post.user_id = regular_user.id
        assert not Guardian(regular_user).can_edit_post(deleted_post)

    def test_can_delete_own_post(self, regular_user, open_post):
        open_post.user_id = regular_user.id
        assert Guardian(regular_user).can_delete_post(open_post)

    def test_cannot_delete_others_post(self, regular_user, open_post, other_user):
        open_post.user_id = other_user.id
        assert not Guardian(regular_user).can_delete_post(open_post)


# ── ensure_* helpers (raise) ──────────────────────────────────────────────────


class TestEnsureHelpers:
    def test_ensure_authenticated_raises_for_anon(self):
        with pytest.raises(HTTPException) as exc:
            Guardian(None).ensure_authenticated()
        assert exc.value.status_code == 401

    def test_ensure_authenticated_passes_for_user(self, regular_user):
        Guardian(regular_user).ensure_authenticated()  # no exception

    def test_ensure_can_see_topic_raises(self, deleted_topic):
        with pytest.raises(PermissionDenied):
            Guardian(None).ensure_can_see_topic(deleted_topic)

    def test_ensure_can_create_topic_raises_for_anon(self):
        with pytest.raises(PermissionDenied):
            Guardian(None).ensure_can_create_topic()

    def test_ensure_can_create_post_raises_for_closed(self, regular_user, closed_topic):
        with pytest.raises(PermissionDenied):
            Guardian(regular_user).ensure_can_create_post(closed_topic)

    def test_ensure_can_edit_post_raises(self, regular_user, open_post, other_user):
        open_post.user_id = other_user.id
        with pytest.raises(PermissionDenied):
            Guardian(regular_user).ensure_can_edit_post(open_post)

    def test_ensure_can_delete_post_raises(self, regular_user, open_post, other_user):
        open_post.user_id = other_user.id
        with pytest.raises(PermissionDenied):
            Guardian(regular_user).ensure_can_delete_post(open_post)

    def test_ensure_staff_raises_for_regular(self, regular_user):
        with pytest.raises(PermissionDenied):
            Guardian(regular_user).ensure_staff()

    def test_ensure_staff_passes_for_admin(self, admin_user):
        Guardian(admin_user).ensure_staff()  # no exception


# ── get_guardian factory ──────────────────────────────────────────────────────


def test_get_guardian_returns_guardian_instance(regular_user):
    g = get_guardian(regular_user)
    assert isinstance(g, Guardian)
    assert g.user is regular_user


def test_get_guardian_anon():
    g = get_guardian(None)
    assert not g.is_authenticated
