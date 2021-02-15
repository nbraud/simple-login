import arrow
from flask import redirect, url_for, request, flash
from flask_admin import expose, AdminIndexView
from flask_admin.actions import action
from flask_admin.contrib import sqla
from flask_login import current_user

from app.models import User, ManualSubscription


class SLModelView(sqla.ModelView):
    column_default_sort = ("id", True)
    column_display_pk = True

    can_edit = False
    can_create = False
    can_delete = False
    edit_modal = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for("auth.login", next=request.url))


class SLAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for("auth.login", next=request.url))

        return redirect("/admin/user")


class UserAdmin(SLModelView):
    column_searchable_list = ["email", "id"]
    column_exclude_list = [
        "salt",
        "password",
        "otp_secret",
        "last_otp",
        "fido_uuid",
        "profile_picture",
    ]
    can_edit = True

    def scaffold_list_columns(self):
        ret = super().scaffold_list_columns()
        ret.insert(0, "upgrade_channel")
        return ret

    @action(
        "education_upgrade",
        "Education upgrade",
        "Are you sure you want to edu-upgrade selected users?",
    )
    def action_edu_upgrade(self, ids):
        upgrade("Edu", ids, is_giveaway=True)

    @action(
        "charity_org_upgrade",
        "Charity Organization upgrade",
        "Are you sure you want to upgrade selected users using the Charity organization program?",
    )
    def action_charity_org_upgrade(self, ids):
        upgrade("Charity Organization", ids, is_giveaway=True)

    @action(
        "cash_upgrade",
        "Cash upgrade",
        "Are you sure you want to cash-upgrade selected users?",
    )
    def action_cash_upgrade(self, ids):
        upgrade("Cash", ids, is_giveaway=False)

    @action(
        "monero_upgrade",
        "Monero upgrade",
        "Are you sure you want to monero-upgrade selected users?",
    )
    def action_monero_upgrade(self, ids):
        upgrade("Monero", ids, is_giveaway=False)


def upgrade(way: str, ids: [int], is_giveaway: bool):
    query = User.query.filter(User.id.in_(ids))

    for user in query.all():
        if user.is_premium() and not user.in_trial():
            continue

        ManualSubscription.create(
            user_id=user.id,
            end_at=arrow.now().shift(years=1, days=1),
            comment=way,
            is_giveaway=is_giveaway,
            commit=True,
        )

        flash(f"{user} is {way} upgraded")


class EmailLogAdmin(SLModelView):
    column_searchable_list = ["id"]

    can_edit = False
    can_create = False


class AliasAdmin(SLModelView):
    column_searchable_list = ["id", "user.email", "email", "mailbox.email"]


class MailboxAdmin(SLModelView):
    column_searchable_list = ["id", "user.email", "email"]


class LifetimeCouponAdmin(SLModelView):
    can_edit = True
    can_create = True
