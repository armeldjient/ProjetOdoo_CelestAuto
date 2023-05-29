from odoo import fields, models


class ResCompany(models.Model):
	_inherit = "res.company"

	motto = fields.Text(string='Motto')
	siege_social = fields.Text(string='Siege social')
