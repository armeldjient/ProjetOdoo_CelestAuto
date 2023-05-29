import io

from odoo import fields, models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


def get_elements(
    self, quant_obj, location_id, start, end, filter_by, filter_products, category_id
):

    # domains
    quant_domain = [("location_id", "child_of", location_id)]
    moves_domain = [
        ("date", ">=", start),
        ("date", "<=", end),
        ("state", "=", "done"),
        "|",
        ("location_dest_id", "child_of", location_id),
        ("location_id", "child_of", location_id),
    ]
    moves_now_domain = [
        ("date", ">=", end),
        ("date", "<=", fields.Datetime.now()),
        ("state", "=", "done"),
        "|",
        ("location_dest_id", "child_of", location_id),
        ("location_id", "child_of", location_id),
    ]

    if filter_by == "product" and filter_products:
        quant_domain.append(("product_id", "in", filter_products))
        moves_domain.append(("product_id", "in", filter_products))
        moves_now_domain.append(("product_id", "in", filter_products))

    elif filter_by == "category" and category_id:
        categ_id = category_id
        quant_domain.append(("product_id.categ_id", "child_of", categ_id))
        moves_domain.append(("product_id.categ_id", "child_of", categ_id))
        moves_now_domain.append(("product_id.categ_id", "child_of", categ_id))

    quants = quant_obj.search(quant_domain)
    moves = self.env["stock.move"].search(moves_domain)
    moves_to_now = self.env["stock.move"].search(moves_now_domain)

    return (quants, moves, moves_to_now)


def meta_data(data, date_start, date_end, filter_by, filter_products, category_id):

    datas = {}
    datas["warehouse"] = data["warehouse_name"]
    datas["location"] = data["location_name"]
    datas["date_from"] = date_start
    datas["date_to"] = date_end
    datas["details"] = data["details"]
    datas["group_by_category"] = data["group_by_category"]
    datas["filter_category"] = data["category_name"]

    datas["filter_title_label"] = ""
    datas["filter_title_value"] = ""
    if filter_by == "product" and filter_products:
        datas["filter_title_label"] = "Filter Products"
        datas["filter_title_value"] = data["products_name"]
    elif filter_by == "category" and category_id:
        datas["filter_title_label"] = "Filter Categories"
        datas["filter_title_value"] = data["category_name"]

    return datas


def get_values(self, data):

    quant_obj = self.env["stock.quant"]
    products = self.env["product.product"]

    start = data["start"]
    end = data["end"]
    date_start = data["date_start"]
    date_end = data["date_end"]
    location_id = data["location_id"]
    category_id = data["category_id"]
    filter_products = data["products"]
    is_zero = data["is_zero"]
    filter_by = data["filter_by"]
    group_by_category = data["group_by_category"]

    quants, moves, moves_to_now = get_elements(
        self,
        quant_obj,
        location_id,
        start,
        end,
        filter_by,
        filter_products,
        category_id,
    )

    location = self.env["stock.location"].browse(location_id)
    location_ids = self.env["stock.location"].search(
        [("parent_path", "=like", location.parent_path + "%")]
    )

    mv_in = moves.filtered(lambda x: x.location_dest_id.id in location_ids.ids)
    mv_out = moves.filtered(lambda x: x.location_id.id in location_ids.ids)
    mv_tonow_in = moves_to_now.filtered(
        lambda x: x.location_dest_id.id in location_ids.ids
    )
    loc_ids = location_ids.ids
    mv_tonow_out = moves_to_now.filtered(lambda x: x.location_id.id in loc_ids)

    products |= quants.mapped("product_id")
    products |= mv_in.mapped("product_id")
    products |= mv_out.mapped("product_id")
    products = products.sorted(key='name')

    datas = meta_data(
        data, date_start, date_end, filter_by, filter_products, category_id
    )

    result = []
    categories = products.mapped("categ_id")
    categories = categories.sorted(key='name')

    for categ in categories:
        line_categ = {}
        line_categ["name"] = categ.name
        line_categ["lines"] = []

        if group_by_category:
            c_id = categ.id
            products_categ = products.filtered(lambda x: x.categ_id.id == c_id)
            line_categ["show"] = True
        else:
            products_categ = products
            products -= products
            line_categ["show"] = False

        for product in products_categ.sorted(lambda r: r.name):
            variant = product.product_template_attribute_value_ids._get_combination_name()
            line = {}
            line["name"] = product.name and (
                variant and "%s (%s)" % (product.name, variant) or product.name) or False
            line["ref"] = product.default_code
            line["uom"] = product.uom_id.name

            pro_id = product.id
            mv_in_pro = mv_in.filtered(lambda x: x.product_id.id == pro_id)
            mv_out_pro = mv_out.filtered(lambda x: x.product_id.id == pro_id)
            mv_tonow_in_pro = mv_tonow_in.filtered(
                lambda x: x.product_id.id == product.id
            )
            mv_tonow_out_pro = mv_tonow_out.filtered(
                lambda x: x.product_id.id == product.id
            )

            if not is_zero and not mv_in_pro and not mv_out_pro:
                continue

            product_uom = product.uom_id
            tot_in = 0
            for elt in mv_in_pro:
                if product_uom.id != elt.product_uom.id:
                    factor = product_uom.factor / elt.product_uom.factor
                else:
                    factor = 1.0
                tot_in += elt.product_uom_qty * factor

            tot_out = 0
            for elt in mv_out_pro:
                if product_uom.id != elt.product_uom.id:
                    factor = product_uom.factor / elt.product_uom.factor
                else:
                    factor = 1.0
                tot_out += elt.product_uom_qty * factor

            tot_tonow_in = 0
            for elt in mv_tonow_in_pro:
                if product_uom.id != elt.product_uom.id:
                    factor = product_uom.factor / elt.product_uom.factor
                else:
                    factor = 1.0
                tot_tonow_in += elt.product_uom_qty * factor

            tot_tonow_out = 0
            for elt in mv_tonow_out_pro:
                if product_uom.id != elt.product_uom.id:
                    factor = product_uom.factor / elt.product_uom.factor
                else:
                    factor = 1.0
                tot_tonow_out += elt.product_uom_qty * factor

            product_ctxt = product.with_context({"location": location_id})
            actual_qty = product_ctxt.qty_available
            actual_qty += tot_tonow_out - tot_tonow_in

            line["si"] = actual_qty - tot_in + tot_out
            line["in"] = tot_in
            line["out"] = tot_out
            line["bal"] = tot_in - tot_out
            line["fi"] = actual_qty

            line_categ["lines"].append(line)
        result.append(line_categ)


    datas["lines"] = result
    return datas


def get_excel_file(self, data):

    # cree le document
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # format values
    f1_vals = {"font_size": 14, "align": "vcenter", "bold": True}
    f21_vals = {"font_size": 10, "align": "left", "bold": True}
    f3_vals = {"bottom": True, "top": True, "font_size": 12}

    sheet = workbook.add_worksheet("Stock Card")
    format1 = workbook.add_format(f1_vals)
    format21 = workbook.add_format(f21_vals)
    format21_nobold = workbook.add_format(
        {"font_size": 10, "align": "left", "bold": True}
    )
    format3 = workbook.add_format(f3_vals)
    font_size_8_l = workbook.add_format({"font_size": 8, "align": "left"})
    font_size_8_r = workbook.add_format({"font_size": 8, "align": "right"})
    red_mark = workbook.add_format({"font_size": 8, "bg_color": "red"})
    justify = workbook.add_format({"font_size": 12})
    format3.set_align("center")
    justify.set_align("justify")
    format1.set_align("center")
    red_mark.set_align("center")

    format_tab_entete = workbook.add_format(
        {"font_size": 10, "align": "center", "bold": True}
    )
    format_tab_entete.set_bg_color("#333333")
    format_tab_entete.set_font_color("white")
    format_tab_entete.set_align("center")

    sheet.set_column('B:B', 12)  # Column  B   width set to 12.
    sheet.set_column('C:C', 30)  # Column  C   width set to 30.
    sheet.set_column('E:E', 12)  # Column  E   width set to 12.
    sheet.set_column('I:I', 12)  # Column  I   width set to 12.

    sheet.merge_range(2, 1, 2, 2, "Warehouse", format21)
    sheet.merge_range(2, 3, 2, 4, data["warehouse"], format21_nobold)

    if data["filter_title_label"]:
        sheet.write(3, 1, "Location", format21)
        sheet.merge_range(3, 2, 3, 3, data["location"], format21_nobold)
        sheet.write(3, 4, data["filter_title_label"], format21)
        f21_nobold = format21_nobold
        sheet.merge_range(3, 5, 3, 6, data["filter_title_value"], f21_nobold)
    else:
        sheet.merge_range(3, 1, 3, 3, "Location", format21)
        sheet.merge_range(3, 4, 3, 5, data["location"], format21_nobold)

    sheet.write(4, 1, "Date from", format21)
    sheet.write(4, 2, data["date_from"], format21_nobold)
    sheet.write(4, 3, "Date to", format21)
    sheet.write(4, 4, data["date_to"], format21_nobold)

    sheet.write(6, 1, "Reference", format_tab_entete)
    sheet.write(6, 2, "Designation", format_tab_entete)
    sheet.write(6, 3, "Uom", format_tab_entete)
    sheet.write(6, 4, "Stock initial", format_tab_entete)
    sheet.write(6, 5, "In", format_tab_entete)
    sheet.write(6, 6, "Out", format_tab_entete)
    sheet.write(6, 7, "Balance", format_tab_entete)
    sheet.write(6, 8, "Final stock", format_tab_entete)

    i = 7

    for categ in data["lines"]:

        if categ["show"]:
            sheet.merge_range(i, 1, i, 2, "Category", font_size_8_l)
            sheet.merge_range(i, 3, i, 10, categ["name"], format21)
            i += 1

        for line in categ["lines"]:
            sheet.write(i, 1, line["ref"], font_size_8_l)
            sheet.write(i, 2, line["name"], font_size_8_l)
            sheet.write(i, 3, line["uom"], font_size_8_l)
            sheet.write(i, 4, line["si"], font_size_8_r)
            sheet.write(i, 5, line["in"], font_size_8_r)
            sheet.write(i, 6, line["out"], font_size_8_r)
            sheet.write(i, 7, line["bal"], font_size_8_r)
            sheet.write(i, 8, line["fi"], font_size_8_r)
            i += 1
    return workbook, output


class StockCardReport(models.AbstractModel):
    _name = "report.hyd_stock_card.stock_card_template"

    def _get_report_values(self, docids, data=None):

        return {"doc_ids": docids, "data": get_values(self, data)}
