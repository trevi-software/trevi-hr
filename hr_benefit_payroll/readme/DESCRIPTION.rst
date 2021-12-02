Apply Employee Benefits to Payroll
==================================
* Benefits can be linked to payroll
    * Choose the 'Allowance' type for earnings
    * Choose the 'Deduction' type for premiums
    * Use Salary Rules to integrate them in to Payroll Structures
    * Information about the benefits are available to Salary Rules in a top-level 'benefits' dictionary
        - Example: result = benefits.<CODE>.premium_amount
    * The available fields are:
        - qty: the number of policies of this type found
        - advantage_amount: the money to add
        - premium_amount: the money to deduct
        - ppf (Percentage Payroll Factor): 1 if the policy was active for the entire payroll period; less than 1 if it was active only for a fraction of the payroll period
