from odoo import fields, models


class HrEmployeeWebcam(models.TransientModel):
    _name = "hr.employee.webcam"
    _description = "Webcam Form"

    def _compute_employee(self):
        eid = False
        if self.env.context.get("active_id", False):
            eid = self.env.context.get("active_id")
        return eid

    employee_id = fields.Many2one("hr.employee", "Employee", default=_compute_employee)
