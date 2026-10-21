This module implements notifications on employee contracts and allows an
employee to have more than one contract at a time.

- Get notified when an employee is near the end of their trial period
- Get notified when an employee's contract is about to expire
- Allow an employee to have several contracts running at the same time

Since Odoo 19 the contract data lives on `hr.version` (the former
`hr.contract`): a contract is described by its `contract_date_start`,
`contract_date_end`, `trial_date_end` and `date_version` dates and by the
native `active`, `is_current`, `is_past`, `is_future` and `is_in_contract`
flags. The scheduled action shipped by this module is what sets the
"Trial Period Ending" / "Contract Period Ending" alerts.