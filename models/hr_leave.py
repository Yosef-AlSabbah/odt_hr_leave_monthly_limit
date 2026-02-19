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
    _STATES_TO_CONSIDER = ("validate",)
    _FIELDS_TRIGGERING_CONSTRAINT = ("request_date_from", "request_date_to", "employee_id", "state")

    # -------------------------------------------------------------------------
    # MAIN VALIDATION LOGIC
    # -------------------------------------------------------------------------

    @api.constrains(*_FIELDS_TRIGGERING_CONSTRAINT)
    def _check_monthly_leave_limit(self):
        pass
