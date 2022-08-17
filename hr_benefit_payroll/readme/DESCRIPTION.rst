Apply Employee Benefits to Payroll
==================================
* Benefits can be linked to payroll
    * Choose the 'Allowance' type for earnings
    * Choose the 'Deduction' type for premiums
    * Use Salary Rules to integrate them in to Payroll Structures
    * Information about the benefits are available to Salary Rules in a top-level 'benefits' object
        - Example: result = hr_benefit.<CODE>.deductions
    * The available fields are:
        - qty: the number of policies of this type found
        - earnings: the money to add
        - deductions: the money to deduct
        - ppf (Percentage Payroll Factor): 1 if the policy was active for the entire payroll period; less than 1 if it was active only for a fraction of the payroll period
