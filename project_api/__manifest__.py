{
    'name': "project_api",

    'summary': "Sale",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Sale',
    'version': '0.1',

    'depends': ['base', 'sale_management', 'product', 'account_accountant', 'currency_rate_live'],

    'data': [
        'data/multy_currency_update.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
