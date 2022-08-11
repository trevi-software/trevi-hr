
<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->
[![Pre-commit Status](https://github.com/trevi-software/trevi-hr/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/trevi-software/trevi-hr/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/trevi-software/trevi-hr/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/trevi-software/trevi-hr/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/trevi-software/trevi-hr/branch/14.0/graph/badge.svg)](https://codecov.io/gh/trevi-software/trevi-hr)
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
[base_lock](base_lock/) | 14.0.1.0.0 |  | Base locking module.
[group_payroll_manager](group_payroll_manager/) | 14.0.1.0.0 |  | Permissions group Payroll Manager
[hr_accrual_bank](hr_accrual_bank/) | 14.0.1.0.0 |  | Basic framework for recording accruals to a time bank
[hr_attendance_day](hr_attendance_day/) | 14.0.1.0.0 |  | Attach a localized date to an attendace record
[hr_benefit](hr_benefit/) | 14.0.1.0.1 |  | Assign benefits and deductables to employees
[hr_benefit_payroll](hr_benefit_payroll/) | 14.0.1.0.1 |  | Access benefits in payroll through salary rules.
[hr_contract_status](hr_contract_status/) | 14.0.1.0.1 |  | Workflows and notifications on employee contracts.
[hr_contract_status_benefit](hr_contract_status_benefit/) | 14.0.1.0.0 |  | Link hr_contract_status with hr_benefit
[hr_contract_values](hr_contract_values/) | 14.0.1.0.0 |  | Contracts - Initial Settings
[hr_contract_values_payroll](hr_contract_values_payroll/) | 14.0.1.1.0 |  | Contract Payroll Structure Initial Settings
[hr_contract_values_resource_schedule](hr_contract_values_resource_schedule/) | 14.0.1.0.0 |  | Set working hours in default contract values.
[hr_employee_seniority_months](hr_employee_seniority_months/) | 14.0.1.0.1 |  | Calculate an employee's months of employment
[hr_employee_status](hr_employee_status/) | 14.0.1.0.2 |  | Track the HR status of employees
[hr_employee_status_benefit](hr_employee_status_benefit/) | 14.0.1.0.0 |  | Link between hr_employee_status and hr_benefit
[hr_employee_status_payroll](hr_employee_status_payroll/) | 14.0.1.0.0 |  | Adds access records to employee separation records
[hr_employee_wizard](hr_employee_wizard/) | 14.0.1.0.0 |  | Streamline the creation of a new employee record
[hr_job_change_state](hr_job_change_state/) | 14.0.1.0.0 |  | Change State of Jobs
[hr_job_transfer](hr_job_transfer/) | 14.0.1.0.0 |  | Departmental Transfer
[hr_jobs_hierarchy](hr_jobs_hierarchy/) | 14.0.1.0.0 |  | Job Hierarchy
[hr_leave_type_unique](hr_leave_type_unique/) | 14.0.1.0.0 |  | Ensure leave types are unique
[hr_photobooth](hr_photobooth/) | 14.0.1.0.0 |  | Capture employee picture with webcam
[ir_module_category_payroll](ir_module_category_payroll/) | 14.0.1.0.0 |  | Creates Payroll module category
[payroll_payslip_amendment](payroll_payslip_amendment/) | 14.0.1.0.0 |  | Add amendments to current and future pay slips
[payroll_payslip_amendment_contract_status](payroll_payslip_amendment_contract_status/) | 14.0.1.0.0 |  | Link payslip amendments with the employee contract state.
[payroll_payslip_dictionary](payroll_payslip_dictionary/) | 14.0.1.0.0 |  | Dictionary of values that can be used in payslip calculations
[payroll_payslip_hr_leave_type](payroll_payslip_hr_leave_type/) | 14.0.1.0.0 |  | Use time-off codes (instead of names) in payslip rules
[payroll_payslip_patch](payroll_payslip_patch/) | 14.0.1.0.0 |  | Miscellaneous source code patches to payslip handling
[payroll_payslip_report](payroll_payslip_report/) | 14.0.1.0.0 |  | Comprehensive payslip report by department.
[payroll_period_account](payroll_period_account/) | 14.0.1.0.0 |  | Links payroll periods to accounting
[payroll_period_base_lock](payroll_period_base_lock/) | 14.0.1.0.0 |  | Adds a base lock field to a payroll period.
[payroll_period_contract_values](payroll_period_contract_values/) | 14.0.1.0.0 |  | Links payroll period schedules with employee contracts.
[payroll_period_payslip_amendment](payroll_period_payslip_amendment/) | 14.0.1.0.0 |  | Link payslip amendments with a payroll period.
[payroll_period_processing](payroll_period_processing/) | 14.0.1.2.1 |  | Payroll period processing wizard
[payroll_periods](payroll_periods/) | 14.0.1.1.4 |  | Configurable payroll schedules.
[payroll_policy_absence](payroll_policy_absence/) | 14.0.1.0.0 |  | Define properties of an employee absense policy for payroll.
[payroll_policy_accrual](payroll_policy_accrual/) | 14.0.1.0.0 |  | Automatically or manually accrue to time banks to be withdrawn later
[payroll_policy_group](payroll_policy_group/) | 14.0.1.0.1 |  | Group payroll policies and assign them to contracts
[payroll_policy_ot](payroll_policy_ot/) | 14.0.1.0.0 |  | Assign over-time policies to a policy group
[payroll_policy_payslip](payroll_policy_payslip/) | 14.0.1.0.0 |  | Apply payroll policies duing payslip processing
[payroll_policy_presence](payroll_policy_presence/) | 14.0.1.0.0 |  | Define properties of an employee presence policy
[payroll_policy_rounding](payroll_policy_rounding/) | 14.0.1.0.0 |  | Define attendance check-in and check-out rounding policies
[payroll_register](payroll_register/) | 14.0.1.0.0 |  | Payroll Register
[res_currency_denomination](res_currency_denomination/) | 14.0.1.0.0 |  | Currency Denominations
[resource_schedule](resource_schedule/) | 14.0.1.0.0 |  | Easily create, manage, and track employee shift planning.
[trevi_hr_job_categories](trevi_hr_job_categories/) | 14.0.1.0.0 |  | Job Categories
[trevi_hr_usability](trevi_hr_usability/) | 14.0.1.0.0 |  | Simplify Employee Records.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to TREVI Software
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
