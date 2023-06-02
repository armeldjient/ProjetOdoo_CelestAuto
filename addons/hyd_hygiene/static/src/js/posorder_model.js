odoo.define('hyd_hygiene.pos_hyg', function (require) {
"use strict";

var { Order } = require('point_of_sale.models');
var Registries = require('point_of_sale.Registries');

const PosHygOrder = (Order) => class PosHygOrder extends Order {
    constructor() {
        super(...arguments);
        this.to_invoice     = true;
    }

}
Registries.Model.extend(Order, PosHygOrder);

});