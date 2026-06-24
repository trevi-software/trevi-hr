
<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->
[![Pre-commit Status](https://github.com/trevi-software/trevi-hr/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/trevi-software/trevi-hr/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/trevi-software/trevi-hr/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/trevi-software/trevi-hr/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/trevi-software/trevi-hr/branch/16.0/graph/badge.svg)](https://codecov.io/gh/trevi-software/trevi-hr)
<!-- /!\ Non OCA Context : Set here the badge of your translation instance. -->

<!-- /!\ do not modify above this line -->

# TREVI Human Resource addons for Odoo

This repository contains Human Resource addons developed by TREVI Software

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[base_lock](base_lock/) | 16.0.1.0.0 |  | Base locking module.
[hr_accrual_bank](hr_accrual_bank/) | 16.0.1.0.0 |  | Basic framework for recording accruals to a time bank
[hr_attendance_day](hr_attendance_day/) | 16.0.1.0.0 |  | Attach a localized date to an attendace record
[hr_benefit](hr_benefit/) | 16.0.1.0.0 |  | Assign benefits and deductables to employees
[hr_benefit_payroll](hr_benefit_payroll/) | 16.0.1.0.0 |  | Access benefits in payroll through salary rules.
[hr_contract_status](hr_contract_status/) | 16.0.1.0.0 |  | Workflows and notifications on employee contracts.
[hr_contract_status_benefit](hr_contract_status_benefit/) | 16.0.1.0.0 |  | Link hr_contract_status with hr_benefit
[hr_contract_values](hr_contract_values/) | 16.0.1.0.0 |  | Contracts - Initial Settings
[hr_contract_values_payroll](hr_contract_values_payroll/) | 16.0.1.0.0 |  | Contract Payroll Structure Initial Settings
[hr_contract_values_resource_schedule](hr_contract_values_resource_schedule/) | 16.0.1.0.0 |  | Set working hours in default contract values.
[hr_data_import](hr_data_import/) | 16.0.1.0.0 |  | Import HR data from another system using Excel
[hr_employee_seniority_months](hr_employee_seniority_months/) | 16.0.1.0.0 |  | Calculate an employee's months of employment
[hr_employee_status](hr_employee_status/) | 16.0.1.0.0 |  | Track the HR status of employees
[hr_employee_status_benefit](hr_employee_status_benefit/) | 16.0.1.0.0 |  | Link between hr_employee_status and hr_benefit
[hr_employee_status_payroll](hr_employee_status_payroll/) | 16.0.1.0.0 |  | Adds access records to employee separation records
[hr_employee_wizard](hr_employee_wizard/) | 16.0.1.0.0 |  | Streamline the creation of a new employee record
[hr_job_change_state](hr_job_change_state/) | 16.0.1.0.0 |  | Change State of Jobs
[hr_job_transfer](hr_job_transfer/) | 16.0.1.0.0 |  | Departmental Transfer
[hr_jobs_hierarchy](hr_jobs_hierarchy/) | 16.0.1.0.0 |  | Job Hierarchy
[hr_leave_type_unique](hr_leave_type_unique/) | 16.0.1.0.0 |  | Ensure leave types are unique
[hr_leave_type_unique_preinstall](hr_leave_type_unique_preinstall/) | 16.0.1.0.0 |  | Technical module depended on by Leave Type Unique
[hr_photobooth](hr_photobooth/) | 16.0.1.0.0 |  | Capture employee picture with webcam
[resource_schedule](resource_schedule/) | 16.0.1.0.0 |  | Easily create, manage, and track employee shift planning.
[trevi_hr_job_categories](trevi_hr_job_categories/) | 16.0.1.0.0 |  | Job Categories
[trevi_hr_usability](trevi_hr_usability/) | 16.0.1.0.0 |  | Simplify Employee Records.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to TREVI Software
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
