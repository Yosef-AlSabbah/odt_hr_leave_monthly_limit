# -*- coding: utf-8 -*-
"""
HR Leave Model Extension for Monthly Leave Limit.
"""

from odoo import api, models


class HrLeave(models.Model):
    """
    HR Leave Model Extension to force monthly leave limit.
    """

    _inherit = "hr.leave"

    # -------------------------------------------------------------------------
    # CONFIGURATION
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
    def _check_monthly_leave_limit(self):
        for rec in self:

            # Skip validation in case of not considered states
            if rec.state not in self._STATES_TO_CONSIDER:
                continue

            # Skip validation if employee or request_date_from is not set
            if not (rec.employee_id and rec.request_date_from):
                continue

            rec._check_month_limit_for_record()

    def _check_month_limit_for_record(self):
        """
        The core function to validate the month limit for record.
        """
        if not self.employee_id.resource_calendar_id:
            return

        # Total number of leave days in month with the current leave included
        total_days = self._get_number_of_leaves_for_month(
            self.employee_id, self.request_date_from
        )

        # Check if the total number if leave days in the month exceeds the limit
        if total_days > self._MONTHLY_LEAVE_LIMIT:
            from odoo.exceptions import ValidationError
            from odoo import _

            raise ValidationError(
                _(
                    "You cannot request more than %s working leave days in the month. You have already requested %s days in this month."
                )
                % (self._MONTHLY_LEAVE_LIMIT, total_days - self.number_of_days)
            )

    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def _get_month_bounds(target_date):
        """
        Helper method to get the start and end dates of the month for a given date.

        returns: tuple of datetime objects representing the start and end of the month
        """
        from calendar import monthrange
        from datetime import datetime, time

        number_of_days_in_month = monthrange(target_date.year, target_date.month)[1]
        month_start = target_date.replace(day=1)
        month_end = target_date.replace(day=number_of_days_in_month)

        return (
            datetime.combine(month_start, time.min),
            datetime.combine(month_end, time.max),
        )

    def _get_working_days_in_month(self, employee, target_date):
        """
        Helper method to calculate the number of working days for an employee,
        with and without considering leaves, and returns both values.
        """

        # Get the start & end of the month
        month_start, month_end = self._get_month_bounds(target_date)

        # Calculate the working days in the month with considering leaves
        working_days_in_month_with_leaves = employee._get_work_days_data_batch(
            month_start,
            month_end,
            compute_leaves=True,
            calendar=employee.resource_calendar_id,
        )[employee.id]["days"]

        # Calculate the working days in the month without considering leaves
        working_days_in_month_without_leaves = employee._get_work_days_data_batch(
            month_start,
            month_end,
            compute_leaves=False,
            calendar=employee.resource_calendar_id,
        )[employee.id]["days"]

        return working_days_in_month_with_leaves, working_days_in_month_without_leaves

    def _get_number_of_leaves_for_month(self, employee, target_date):
        """
        Helper Method to Calculate the number of leave days used by the employee in the month of the target date.
        """

        working_days_in_month_with_leaves, working_days_in_month_without_leaves = (
            self._get_working_days_in_month(employee, target_date)
        )

        return working_days_in_month_without_leaves - working_days_in_month_with_leaves
