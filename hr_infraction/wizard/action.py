# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from ..models.hr_infraction import ACTION_TYPE_SELECTION


class ActionWizard(models.TransientModel):

    _name = "hr.infraction.action.wizard"
    _description = "Choice of Actions for Infraction"

    action_type = fields.Selection(
        string="Action", selection=ACTION_TYPE_SELECTION, required=True
    )
    memo = fields.Text(string="Notes")
    new_job_id = fields.Many2one(string="New Job", comodel_name="hr.job")
    xfer_effective_date = fields.Date(string="Effective Transfer Date")
    effective_date = fields.Date()

    def create_action(self):

        infraction_id = self.env.context.get("active_id", False)
        if not infraction_id:
            return False

        Infraction = self.env["hr.infraction"]
        InfrAction = self.env["hr.infraction.action"]
        InfrWarning = self.env["hr.infraction.warning"]
        ModelData = self.env["ir.model.data"]
        ActWindow = self.env["ir.actions.act_window"]

        vals = {
            "infraction_id": infraction_id,
            "type": self.action_type,
            "memo": self.memo,
        }

        action_id = InfrAction.create(vals)

        # Update state of infraction, if not already done so
        #
        infraction = Infraction.browse(infraction_id)
        if infraction.state == "confirm":
            infraction.action_action()

        # If the action is a warning create the appropriate record,
        # reference it from the action, and pull it up in the view
        # (in case the user needs to make any changes).
        #
        if self.action_type in ["warning_verbal", "warning_letter"]:
            vals = {
                "name": (self.action_type == "warning_verbal" and "Verbal" or "Written")
                + " Warning",
                "type": self.action_type == "warning_verbal" and "verbal" or "written",
                "action_id": action_id.id,
            }
            warning_id = InfrWarning.create(vals)
            action_id.warning_id = warning_id
            res_model, res_id = ModelData.get_object_reference(
                "hr_infraction", "open_hr_infraction_warning"
            )
            dict_action_window = ActWindow.browse(res_id).read()[0]
            dict_action_window["view_mode"] = "form,tree"
            dict_action_window["domain"] = [("id", "=", warning_id.id)]
            return dict_action_window

        # If the action is a departmental transfer create the appropriate record,
        # reference it from the action, and pull it up in the view
        # (in case the user needs to make any changes).
        #
        elif self.action_type == "transfer":
            DptTransfer = self.env["hr.department.transfer"]
            vals = {
                "employee_id": infraction.employee_id.id,
                "src_id": infraction.employee_id.contract_id.job_id.id,
                "dst_id": self.new_job_id.id,
                "src_contract_id": infraction.employee_id.contract_id.id,
                "date": self.xfer_effective_date,
            }
            transfer_id = DptTransfer.create(vals)
            action_id.transfer_id = transfer_id
            res_model, res_id = ModelData.get_object_reference(
                "hr_job_transfer", "open_hr_department_transfer"
            )
            dict_act_window = ActWindow.browse(res_id).read()[0]
            dict_act_window["view_mode"] = "form,tree"
            dict_act_window["demain"] = [("id", "=", transfer_id.id)]
            return dict_act_window

        # The action is dismissal. Begin the termination process.
        elif self.action_type == "dismissal":
            Termination = self.env["hr.employee.termination"]

            # We must create the employment termination object before we set
            # the contract state to 'done'.
            res_model, res_id = ModelData.get_object_reference(
                "hr_infraction", "term_dismissal"
            )
            vals = {
                "employee_id": infraction.employee_id.id,
                "name": self.effective_date,
                "reason_id": res_id,
            }
            termination_id = Termination.create(vals)

            # End any open contracts
            for contract in infraction.employee_id.contract_ids:
                if contract.state not in ["close", "cancel"]:
                    contract.date_end_original = contract.date_end
                    contract.date_end = self.effective_date
                    contract.update_state()

            # Set employee state to pending deactivation
            termination_id.employee_id.set_state_separation()

            res_model, res_id = ModelData.get_object_reference(
                "hr_employee_status", "open_hr_employee_termination"
            )
            dict_act_window = ActWindow.browse(res_id).read()[0]
            dict_act_window["domain"] = [("id", "=", termination_id.id)]
            return dict_act_window

        return True
