import json
from datetime import datetime

import pytz
from openerp.exceptions import Warning as UserError

from odoo import _, api, fields, models
from odoo.tools import date_utils

from odoo.addons.hyd_stock_card import reports

FORMAT_DATE = "%Y-%m-%d %H:%M:%S"
ERREUR_FUSEAU = _("Set your timezone in preferences")


class StockCardWizard(models.TransientModel):
    u"""."""

    _name = "wizard.stock_card_wizard"

    details = fields.Boolean(string="Detailed report", default=False)

    date_start = fields.Datetime(string="Start date", required=True)

    date_end = fields.Datetime(string="End date", required=True)

    location_id = fields.Many2one(
        string="Location", comodel_name="stock.location", required=True
    )

    group_by_category = fields.Boolean(
        string="Group by category", default=False, store=True,
    )

    filter_by = fields.Selection(
        string="Filter by",
        required=True,
        selection=[
            ("no_filter", "No filter"),
            ("product", "Product"),
            ("category", "Category"),
        ],
        default="no_filter",
    )

    products = fields.Many2many(
        string="Produits", comodel_name="product.product", store=True,
    )

    category = fields.Many2one(
        string="Filter category",
        comodel_name="product.category",
        help="Select category to filter",
    )

    is_zero = fields.Boolean(
        string="Include no moves in period",
        default=True,
        help="""Unselect if you just want to see product who have move"""
        """ in the period.""",
    )
    report_file_name = fields.Char(
        string='File name (excel only)',
        compute="compute_report_file_name",
        readonly=False
    )

    @api.model
    def convert_UTC_TZ(self, UTC_datetime):
        if not self.env.user.tz:
            raise UserError(ERREUR_FUSEAU)
        local_tz = pytz.timezone(self.env.user.tz)
        date = datetime.strptime(str(UTC_datetime), FORMAT_DATE)
        date = pytz.utc.localize(date, is_dst=None).astimezone(local_tz)
        return date.strftime(FORMAT_DATE)

    @api.depends('date_start', 'date_end', 'location_id', 'details')
    def compute_report_file_name(self):
        for rec in self:
            suffix = "Stock_details_" if rec.details else "Stock_"
            if rec.location_id:
                suffix += rec.location_id.name
                suffix += "_"
            if rec.date_start:
                suffix += "%d" % rec.date_start.day
                suffix += "_"
                suffix += "%d" % rec.date_start.month
                suffix += "_"
                suffix += "%d" % rec.date_start.year
            suffix += _("_to_")
            if rec.date_end:
                suffix += "%s" % rec.date_end.day
                suffix += "_"
                suffix += "%d" % rec.date_end.month
                suffix += "_"
                suffix += "%d" % rec.date_start.year
            rec.report_file_name = suffix

    def print_card(self):
        """Print the stock card."""
        self.ensure_one()

        location = self.location_id
        warehouse = None
        warehouses = self.env["stock.warehouse"].search([])
        for war in warehouses:
            wlocation = war.view_location_id
            if location.parent_path.startswith(wlocation.parent_path):
                warehouse = war
                break

        context = self.env.context
        is_excel = context.get("xls_export", False)

        datas = {}
        datas["date_start"] = self.convert_UTC_TZ(self.date_start)
        datas["date_end"] = self.convert_UTC_TZ(self.date_end)
        datas["start"] = self.date_start
        datas["end"] = self.date_end
        datas["location_id"] = location.id
        datas["group_by_category"] = self.group_by_category
        datas["filter_by"] = self.filter_by
        datas["category_id"] = self.category.id if self.category else None
        datas["category_name"] = self.category.name if self.category else None
        datas["products"] = self.products.mapped("id")
        datas["products_name"] = ",".join(self.products.mapped("name"))
        datas["location_name"] = location.name
        wareh = warehouse
        datas["warehouse_name"] = wareh.name if wareh else location.name
        datas["details"] = self.details
        datas["is_zero"] = self.is_zero
        datas["report_file_name"] = self.report_file_name

        report_name = "hyd_stock_card.stock_card_report"
        get_exl_vals = reports.stock_card_report.get_values
        if self.details:
            report_name = "hyd_stock_card.stock_card_details_report"
            get_exl_vals = reports.stock_card_details_report.get_values

        if is_excel:
            json_default = date_utils.json_default
            return {
                "type": "ir.actions.report",
                "report_type": "hyd_xlsx_download",
                "data": {
                    "model": "wizard.stock_card_wizard",
                    "options": json.dumps(
                        get_exl_vals(self, datas), default=json_default
                    ),
                    "output_format": "xlsx",
                    "report_name": self.report_file_name,
                },
            }
        else:
            return self.env.ref(report_name).report_action(self, data=datas)

    def get_xlsx_report(self, data, response):

        s = reports.stock_card_details_report
        if not data["details"]:
            s = reports.stock_card_report

        excel_method = s.get_excel_file
        workbook, output = excel_method(self, data)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
