# -*- coding: utf-8 -*-
{
    'name': "eBaySendProduct",

    'summary': """
       With this module  you will be able to send  the products of your company to eBay""",

    'description': """
        Con este modulo podras subir los productos de tu propia compañia y ampliar tus mercados también a la página de eBay
    """,

    'author': "Sergio Algara",
    #'website': "http://www.propia.sedrftg",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'eBayCategory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'registration_view.xml',
        'add_article_view.xml'
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
