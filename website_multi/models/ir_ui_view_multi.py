# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class IrUiViewMulti(models.Model):
    _name = 'ir.ui.view.multi'

    inherit_id = fields.Many2one(comodel_name='ir.ui.view', required=True)
    view_id = fields.Many2one(comodel_name='ir.ui.view', required=True)
    theme_id = fields.Many2one(comodel_name='website.theme')
    website_id = fields.Many2one(comodel_name='website.theme')
    active = fields.Boolean(default=True)

    @api.model
    def get_multi_inheriting_views_arch(self, inherit_id):
        website_id = self.env.context.get('website_id', False)
        website = self.env['website'].browse(website_id)
        records = self.search([
            ('inherit_id', '=', inherit_id),
            ('theme_id', 'in', (website.theme_id, False)),
            ('website_id', 'in', (website.id, False)),
            ('active', '=', True),
        ])
        user_groups = frozenset(self.env.user.groups_id or ())
        return [(record.view_id.arch, record.view_id.id)
                for record in records
                if not (record.view_id.groups_id and
                        user_groups.isdisjoint(record.view_id.groups_id))]
