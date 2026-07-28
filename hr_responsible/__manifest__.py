{
    'name': "hr_responsible",

    'summary': """
        Set a default HR responsible for employees.""",

    'description': """
        This module allows you to set a default HR responsible for employees.
    """,

    'author': "TREVI Software",
    'website': "https://github.com/trevi-software/trevi-hr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0.1.0.0',
    'license': "AGPL-3",
    # any module necessary for this one to work correctly
    'depends': ['hr'],

    # always loaded
    'data': [
        'views/res_config_view.xml',
    ],
}
