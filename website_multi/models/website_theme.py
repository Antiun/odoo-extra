# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class WebsiteTheme(models.Model):
    _name = 'website.theme'

    name = fields.Char(required=True)
    css_class = fields.Char(string='CSS class', required=True)
    website_ids = fields.One2many(
        comodel_name='website', inverse_name='theme_id',
        string="Websites")
    website_count = fields.Integer(
        string="# websites", compute='_compute_website_count', store=True)

    @api.multi
    @api.depends('website_ids')
    def _compute_website_count(self):
        for theme in self:
            theme.website_count = len(theme.website_ids)
