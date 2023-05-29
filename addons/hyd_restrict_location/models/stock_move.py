from odoo import _, api, models
from odoo.exceptions import ValidationError

TEMP_MOVE_RESTRICT = _(
    """Only the users: %s \n """ """are allowed to do transfert %s this location\n"""
)


class StockMove(models.Model):
    """."""

    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        """."""
        messages = self.mapped(lambda x: x.check_access_right())
        error_messages = list(filter(lambda elt: elt, messages))
        if len(error_messages) > 0:
            raise ValidationError(error_messages[0])
        return super(StockMove, self)._action_done(cancel_backorder)


    @api.model
    def check_access_right(self):
        message = []
        uid = self.env.user.id
        srcl = self.location_id
        dstl = self.location_dest_id

        if srcl.allowed_users and uid not in srcl.allowed_users.ids:
            allowed = ",".join(srcl.allowed_users.mapped("name"))
            message.append(TEMP_MOVE_RESTRICT % (allowed, "from"))

        if dstl.allowed_users and uid not in dstl.allowed_users.ids:
            allowed = ",".join(dstl.allowed_users.mapped("name"))
            message.append(TEMP_MOVE_RESTRICT % (allowed, "to"))

        return message[0] if len(message) > 0 else False
