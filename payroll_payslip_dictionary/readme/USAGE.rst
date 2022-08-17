The new values provided by this module are:
* payroll.max_weekly_hours - the maximum number of weekly work hours
* payroll.max_working_days - the maximum number of working days in the period
* payroll.max_working_hours - the maximum number of working days in the period
* payroll.seniority - the length of employment calculated in months
* payroll.contracts.cummulative_ppf - the sum of the payroll period factors of all the contracts
* current_contract.ppf - the payroll period factor for the contract being processed
* current_contract.daily_wage - the wage on the contract being processed converted to a daily wage
* current_contract.hourly_wage - the wage on the contract being processed converted to an hourly wage

The payroll period factor is a decimal denoting the validity period of the contract between the
start and end dates of the payslip. A factor of 1 means the contract covers the entire
period of the payslip. A value less than one denotes the percentage of the payslip duration
covered by the contract. In this case if the payslip is for the period from April 1 to April 30
and the employee's contract ends on April 15 then the payroll period factor will be 0.5. The
cummulative_ppf is the sum of all the indvidual contracts' ppf.
