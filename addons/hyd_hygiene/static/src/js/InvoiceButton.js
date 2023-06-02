odoo.define('hyd_hygiene.PosHygInvoiceButton', function (require) {
    'use strict';

    const InvoiceButton = require('point_of_sale.InvoiceButton');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const { isConnectionError } = require('point_of_sale.utils');

    const PosHygInvoiceButton = (InvoiceButton) =>
        class extends InvoiceButton {
            async _downloadInvoice(orderId) {
                try {
                    const [orderWithInvoice] = await this.rpc({
                        method: 'read',
                        model: 'pos.order',
                        args: [orderId, ['account_move']],
                        kwargs: { load: false },
                    });
                    if (orderWithInvoice && orderWithInvoice.account_move) {
                        await this.env.legacyActionManager.do_action('hyd_hygiene.report_facture_a5', {
                            additional_context: {
                                active_ids: [orderWithInvoice.account_move],
                            },
                        });
                    }
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        // NOTE: error here is most probably undefined
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Network Error'),
                            body: this.env._t('Unable to download invoice.'),
                        });
                    }
                }
            }
        };

    Registries.Component.extend(InvoiceButton, PosHygInvoiceButton);

    return PosHygInvoiceButton;
});
