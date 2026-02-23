# -*- coding: utf-8 -*-
"""
HR Leave Model Extension for Monthly Leave Limit.
"""

from calendar import monthrange
from datetime import date, datetime, time

from odoo import api, models, _
from odoo.exceptions import ValidationError


class HrLeave(models.Model):
    """
    HR Leave Model Extension to force monthly leave limit.
    """

    _inherit = "hr.leave"

    # -------------------------------------------------------------------------
    # CONFIGURATIONS
    # -------------------------------------------------------------------------

    _MONTHLY_LEAVE_LIMIT = 5
    _STATES_TO_CONSIDER = ("confirm", "validate", "validate1")
    _FIELDS_TRIGGERING_CONSTRAINT = (
        "request_date_from",
        "request_date_to",
        "employee_id",
        "state",
    )

    # -------------------------------------------------------------------------
    # CORE VALIDATION LOGIC
    # -------------------------------------------------------------------------

    @api.constrains(*_FIELDS_TRIGGERING_CONSTRAINT)
    def _check_monthly_leave_limit(self) -> None:
        """
        Constraint to enforce monthly leave limits per employee.
        """
        for rec in self:
            # Skip validation for excluded or irrelevant record states.
            if rec.state not in self._STATES_TO_CONSIDER:
                continue

            # Bypass validation if employee ID or start date is missing.
            if not (rec.employee_id and rec.request_date_from):
                continue

            rec._check_month_limit_for_record()

    def _check_month_limit_for_record(self) -> None:
        """
        Core logic for validating monthly leave limits against the record.
        """

        if self.number_of_days > self._MONTHLY_LEAVE_LIMIT * 2:
            raise ValidationError(
                _("You cannot request more than %s working leave days at a time. ")
                % (self._MONTHLY_LEAVE_LIMIT * 2)
            )

        total_leaves, total_carryover = self._compute_monthly_working_leave_days(
            self.employee_id, self.request_date_from
        )

        # Validate if total monthly leave exceeds the permitted limit.
        if total_leaves > self._MONTHLY_LEAVE_LIMIT:
            raise ValidationError(
                _(
                    "You cannot request more than %s working leave days in this month. "
                    "You have already requested approximately %s days."
                )
                % (self._MONTHLY_LEAVE_LIMIT, round(total_leaves))
            )

        if total_carryover > self._MONTHLY_LEAVE_LIMIT:
            raise ValidationError(
                _(
                    "You cannot request more than %s working leave days in next month. "
                    "You have already requested approximately %s days."
                )
                % (self._MONTHLY_LEAVE_LIMIT, round(total_carryover))
            )

    def _compute_monthly_working_leave_days(
        self, employee, target_date
    ) -> tuple[float, float]:
        """
        Calculates an employee's monthly working leave days and carryover balances.
        """
        month_start_dt, month_end_dt = self._month_start_end_dt(target_date)

        leaves = self._get_related_leaves_for_interval(
            employee, month_start_dt, month_end_dt
        )

        total_leaves = 0.0
        total_carryover = 0.0

        for leave in leaves:
            overlap_start, overlap_end = self._get_date_range_overlap(
                leave.date_from, leave.date_to, month_start_dt, month_end_dt
            )

            if overlap_end <= overlap_start:
                continue

            num_of_days, carry = self._compute_leave_days_within_period(
                employee, leave.number_of_days, overlap_start, overlap_end
            )

            total_leaves += num_of_days
            total_carryover += carry if leave.date_from >= month_start_dt else 0.0

        return total_leaves, total_carryover

    # -------------------------------------------------------------------------
    # HELPER FUNCTION
    # -------------------------------------------------------------------------

    @staticmethod
    def _month_start_end_dt(target_date) -> tuple[datetime, datetime]:
        """
        returns datetime start & end of the month.
        """
        # Determine the first day of the month.
        month_start = date(target_date.year, target_date.month, 1)

        # Get the month's end date, handling leap year logic via monthrange.
        month_end = date(
            target_date.year,
            target_date.month,
            monthrange(target_date.year, target_date.month)[1],
        )

        month_start_dt = datetime.combine(month_start, time.min)
        month_end_dt = datetime.combine(month_end, time.max)

        return month_start_dt, month_end_dt

    def _get_related_leaves_for_interval(self, employee, month_start_dt, month_end_dt):
        """
        Retrieves leave records for a specific employee within a defined date range.
        """
        return employee.env["hr.leave"].search(
            [
                ("employee_id", "=", employee.id),
                ("state", "in", self._STATES_TO_CONSIDER),
                ("date_from", "<=", month_end_dt),
                ("date_to", ">=", month_start_dt),
            ]
        )

    @staticmethod
    def _get_date_range_overlap(
        leave_start, leave_end, period_start, period_end
    ) -> tuple[datetime, datetime]:
        overlap_start = max(leave_start, period_start)
        overlap_end = min(leave_end, period_end)

        return overlap_start, overlap_end

    @staticmethod
    def _compute_leave_days_within_period(
        employee, total_leave_days, start_dt, end_dt
    ) -> tuple[float, float]:
        calender_attendances = employee._get_calendar_attendances(
            start_dt,
            end_dt,
        )

        working_days_leaves = calender_attendances.get("days", 0.0)
        carryover = total_leave_days - working_days_leaves

        return working_days_leaves, carryover
