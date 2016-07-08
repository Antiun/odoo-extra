{
    'name': 'Multi Website',
    'category': 'Website',
    'summary': 'Build Multiple Websites',
    'website': 'https://www.odoo.com',
    'version': '1.0',
    'description': """
OpenERP Multi Website
=====================

        """,
    'author': 'OpenERP SA',
    'depends': ['website'],
    'installable': True,
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/res_config.xml',
        'views/website_views.xml',
        'views/website_admin.xml',
        'views/website_templates.xml',
    ],
    'demo' : [
        'demo/website.xml',
        'demo/website_2.xml',
        'demo/template.xml',
        'demo/template_2.xml',
    ],
    'application': True,
}
