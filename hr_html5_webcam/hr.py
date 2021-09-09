from openerp.osv import osv


class HrEmployee(osv.Model):

    _name = "hr.employee"
    _inherit = "hr.employee"

    def action_take_picture(self):

        res_id = self.env.ref("hr_webcam.action_take_photo")
        dict_act_window = self.env["ir.actions.client"].read(res_id, [])
        if not dict_act_window.get("params", False):
            dict_act_window.update({"params": {}})
        dict_act_window["params"].update({"employee_id": self.id or False})
        return dict_act_window
