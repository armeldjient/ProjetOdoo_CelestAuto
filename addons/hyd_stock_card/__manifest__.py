{
    "name": "Stock card (PDF & Excel)",
    "summary": "Add an report stock card in inventory",
    "description": """
        Print stock card.

        Print a stock card for a location wether it is for a internal,
        view, inventory, production or scrapped location. This module
        will give you the in, out and the balance of location between
        a period.
    """,
    "author": "HyD Freelance",
    "website": "http://",
    "category": u"Warehouse",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "depends": ["stock", "web"],
    "data": [
        # reports
        "reports/stock_card_report.xml",
        "reports/stock_card_details_report.xml",
        # views
        # wizards
        "wizards/stock_card_wizard_views.xml",
        # security
        "security/ir.model.access.csv",
    ],
    'assets': {
        'web.assets_backend': [
            'hyd_stock_card/static/src/js/*.js',
        ],
        'web.assets_qweb': [
            'hyd_stock_card/static/src/xml/*.xml',
        ],
    },
    "demo": [],
    "installable": True,
    "price": 80,
    "currency": "EUR",
    "images": ["static/images/main_screenshot.png"],
}
