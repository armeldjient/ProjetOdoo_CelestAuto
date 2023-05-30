from odoo import api, fields, models


class AccountMove(models.Model):
	_inherit = "account.move"

	def _amount_in_word (self):
	    for rec in self:
	        rec.word_amount_total = str(rec.currency_id.amount_to_text(rec.amount_total))

	word_amount_total = fields.Char(
		string="Amount Total In Word",
		compute='_amount_in_word'
	)

	pos_order_id = fields.Many2one(
	    comodel_name='pos.order',
	    string='Pos Order',
	    compute="_compute_pos_order_id",
	    store=True,
	    readonly=True
	)

	@api.depends('ref')
	def _compute_pos_order_id(self):
		orders = self.env["pos.order"].search([('name', 'in', self.mapped('ref'))])
		for rec in self:
			order = None
			curr_order = orders.filtered(lambda x: x.name == rec.ref)
			if len(curr_order) > 0:
				order = curr_order[0].id
			rec.update({'pos_order_id': order})
