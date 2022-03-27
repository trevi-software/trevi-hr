[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/trevi-hr&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/trevi-hr/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/trevi-hr/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/trevi-hr/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/trevi-hr/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/trevi-hr/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/trevi-hr)
[![Translation Status](https://translation.odoo-community.org/widgets/trevi-hr-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/trevi-hr-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# TREVI Human Resource addons for Odoo

This repository contains Human Resource addons developed by TREVI Software

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | summary
--- | --- | ---
[base_lock](base_lock/) | 14.0.1.0.0 | Base locking module.
[group_payroll_manager](group_payroll_manager/) | 14.0.1.0.0 | Permissions group Payroll Manager
[hr_accrual_bank](hr_accrual_bank/) | 14.0.1.0.0 | Basic framework for recording accruals to a time bank
[hr_benefit](hr_benefit/) | 14.0.1.0.0 | Assign benefits and deductables to employees
[hr_benefit_payroll](hr_benefit_payroll/) | 14.0.1.0.0 | Access benefits in payroll through salary rules.
[hr_contract_status](hr_contract_status/) | 14.0.1.0.1 | Workflows and notifications on employee contracts.
[hr_contract_values](hr_contract_values/) | 14.0.1.0.0 | Contracts - Initial Settings
[hr_contract_values_payroll](hr_contract_values_payroll/) | 14.0.1.1.0 | Contract Payroll Structure Initial Settings
[hr_employee_seniority_months](hr_employee_seniority_months/) | 14.0.1.0.0 | Calculate an employee's months of employment
[hr_employee_status](hr_employee_status/) | 14.0.1.0.2 | Track the HR status of employees
[hr_employee_status_payroll](hr_employee_status_payroll/) | 14.0.1.0.0 | Adds access records to employee separation records
[hr_job_change_state](hr_job_change_state/) | 14.0.1.0.0 | Change State of Jobs
[hr_job_transfer](hr_job_transfer/) | 14.0.1.0.0 | Departmental Transfer
[hr_jobs_hierarchy](hr_jobs_hierarchy/) | 14.0.1.0.0 | Job Hierarchy
[hr_leave_type_unique](hr_leave_type_unique/) | 14.0.1.0.0 | Ensure leave types are unique
[hr_photobooth](hr_photobooth/) | 14.0.1.0.0 | Capture employee picture with webcam
[ir_module_category_payroll](ir_module_category_payroll/) | 14.0.1.0.0 | Creates Payroll module category
[payroll_payslip_amendment](payroll_payslip_amendment/) | 14.0.1.0.0 | Add amendments to current and future pay slips
[payroll_payslip_amendment_contract_status](payroll_payslip_amendment_contract_status/) | 14.0.1.0.0 | Link payslip amendments with the employee contract state.
[payroll_period_account](payroll_period_account/) | 14.0.1.0.0 | Links payroll periods to accounting
[payroll_period_base_lock](payroll_period_base_lock/) | 14.0.1.0.0 | Adds a base lock field to a payroll period.
[payroll_period_contract_values](payroll_period_contract_values/) | 14.0.1.0.0 | Links payroll period schedules with employee contracts.
[payroll_period_payslip_amendment](payroll_period_payslip_amendment/) | 14.0.1.0.0 | Link payslip amendments with a payroll period.
[payroll_period_processing](payroll_period_processing/) | 14.0.1.0.0 | Payroll period processing wizard
[payroll_periods](payroll_periods/) | 14.0.1.1.2 | Configurable payroll schedules.
[payroll_policy_absence](payroll_policy_absence/) | 14.0.1.0.0 | Define properties of an employee absense policy for payroll.
[payroll_policy_accrual](payroll_policy_accrual/) | 14.0.1.0.0 | Automatically or manually accrue to time banks to be withdrawn later
[payroll_policy_group](payroll_policy_group/) | 14.0.1.0.0 | Group payroll policies and assign them to contracts
[payroll_policy_ot](payroll_policy_ot/) | 14.0.1.0.0 | Assign over-time policies to a policy group
[payroll_policy_presence](payroll_policy_presence/) | 14.0.1.0.0 | Define properties of an employee presence policy
[payroll_register](payroll_register/) | 14.0.1.0.0 | Payroll Register
[res_currency_denomination](res_currency_denomination/) | 14.0.1.0.0 | Currency Denominations
[trevi_hr_job_categories](trevi_hr_job_categories/) | 14.0.1.0.0 | Job Categories
[trevi_hr_public_holidays](trevi_hr_public_holidays/) | 14.0.1.0.0 | Public Holidays
[trevi_hr_usability](trevi_hr_usability/) | 14.0.1.0.0 | Simplify Employee Records.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to OCA
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
