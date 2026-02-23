# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import ValidationError

from dateutil.relativedelta import relativedelta
from pytz import timezone, utc


class HrLeave(models.Model):
    """
    HR Leave Model Extension to force monthly leave limit.
    """

    _inherit = "hr.leave"

    def _get_affected_months(self):
        self.ensure_one()
        if not self.date_from or not self.date_to:
            return []

        employee_tz = timezone(
            self.employee_id.resource_calendar_id.tz or self.env.user.tz or "UTC"
        )

        local_date_from = utc.localize(self.date_from).astimezone(employee_tz)
        local_date_to = utc.localize(self.date_to).astimezone(employee_tz)

        months = []
        current = local_date_from.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        while current <= local_date_to:
            month_end_local = (
                current + relativedelta(months=1) - relativedelta(seconds=1)
            )

            month_start_utc = (
                employee_tz.localize(current.replace(tzinfo=None))
                .astimezone(utc)
                .replace(tzinfo=None)
            )

            month_end_utc = (
                employee_tz.localize(month_end_local.replace(tzinfo=None))
                .astimezone(utc)
                .replace(tzinfo=None)
            )

            months.append((month_start_utc, month_end_utc))
            current += relativedelta(months=1)

        return months

    def _get_monthly_limit_hours(self, employee):
        daily_hours = employee.resource_calendar_id.hours_per_day or 8.0
        return daily_hours * 5

    def _get_working_hours_in_range(self, employee, date_from, date_to):
        if not employee or not date_from or not date_to:
            return 0.0
        work_time = employee._list_work_time_per_day(date_from, date_to)
        return sum(hours for _date, hours in work_time.get(employee.id, []))

    def _get_existing_monthly_hours(self, employee, month_start, month_end):
        existing_leaves = self.env["hr.leave"].search(
            [
                ("employee_id", "=", employee.id),
                ("date_from", "<", month_end),
                ("date_to", ">", month_start),
                ("state", "in", ["validate", "validate1", "confirm"]),
                ("id", "not in", self.ids),
            ]
        )

        total = 0.0
        for leave in existing_leaves:
            portion_start = max(leave.date_from, month_start)
            portion_end = min(leave.date_to, month_end)
            total += self._get_working_hours_in_range(
                employee, portion_start, portion_end
            )
        return total

    def _check_monthly_limit(self):
        for leave in self:
            if leave.state in ["refuse", "cancel"]:
                continue

            if not leave.date_from or not leave.date_to:
                continue

            monthly_limit = self._get_monthly_limit_hours(leave.employee_id)

            for month_start, month_end in leave._get_affected_months():

                portion_start = max(leave.date_from, month_start)
                portion_end = min(leave.date_to, month_end)

                current_hours = self._get_working_hours_in_range(
                    leave.employee_id, portion_start, portion_end
                )

                existing_hours = self._get_existing_monthly_hours(
                    leave.employee_id, month_start, month_end
                )

                total = current_hours + existing_hours

                if total > monthly_limit:
                    raise ValidationError(
                        _(
                            "%(employee)s cannot take more than 5 working days off in one month.\n"
                            "Already taken: %(existing).1f hours\n"
                            "This request:  %(current).1f hours",
                            employee=leave.employee_id.name,
                            existing=existing_hours,
                            current=current_hours,
                        )
                    )

    @api.constrains("date_from", "date_to", "employee_id", "state")
    def _constrains_monthly_limit(self):
        self._check_monthly_limit()