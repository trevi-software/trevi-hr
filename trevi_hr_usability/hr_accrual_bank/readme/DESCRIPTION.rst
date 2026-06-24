Accruals to Bank
================

An Accrual is any benefit (usually time) that accrues on behalf of an employee over an extended
period of time. This can be vacation days, sick days, or some other benefit. The actual policy
and mechanics of bank accrual should be handled by other modules. This module only provides
the basic framework for recording the data. While this module's functionality overlaps with
Odoo's accrual leave allocations they are not the same and are not interchangeable. Specifically, this
module:
* Allows more complex accrual accounting (for example 1.5 days for every month for the first 12 months, then 1.75 days for the next 12 months, etc...)
* Allows creation of accruals from salary rules during payroll processing
* Does not attach units to the accrued amount (1.0 can mean a vacation day, a dollar, a product, or anything else depending on the module)
