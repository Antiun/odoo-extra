from lxml import etree

from openerp import tools
from openerp.osv import osv, fields, orm
from openerp import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

# TODO
# - Use also website.theme_id para filtrar las vistas que aplican
#       - pages
#       - layout
#
# - Add compute field to know if this view inherit from website.layout
#   - Because inherit directly
#   - Because inherit indirectly


#class IrUiView(models.Model):
#    _inherit = "ir.ui.view"

#    def _view_obj(self, cr, uid, view_id, context=None):
#        - First filter by website_id
#        - Then filter by website_id.theme
#        - Then super

#    def get_inheriting_views_arch(self, cr, uid, view_id, model, context=None):
#        - Add also templates with theme_id = current_website.theme_id

class view(osv.osv):

    _inherit = "ir.ui.view"

    def _get_is_layout(self, cr, uid, ids, name, arg, context=None):
        result = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            current = record
            while current:
                if 'website.layout' in (current.key, current.xml_id):
                    result[record.id] = True
                    break
                current = current.inherit_id
        return result

    _columns = {
        'website_id': fields.many2one('website', ondelete='cascade', string="Website", copy=False),
        'theme_id': fields.many2one('website.theme', ondelete='cascade', string="Theme", copy=False),
        # 'multi_inherit_ids': fields.many2many('ir.ui.view', id1='id', id2='id', string="Multi inherit", copy=False),
        'key': fields.char('Key'),
        'is_layout': fields.function(
            _get_is_layout,
            type='boolean',
            string='Is website layout?',
            store={
                'ir.ui.view': (lambda self, cr, uid, ids, c=None: ids, ['inherit_id', 'key'], 10)
            },
        ),
    }

    _sql_constraints = [(
        'key_website_id_unique',
        'unique(key, website_id)',
        'Key must be unique per website.'
    )]

    def _view_obj(self, cr, uid, view_id, context=None):
        # _logger.info('_view_obj: view_id = %s', view_id)
        # _logger.info('_view_obj: context = %s', context)
        context = context or {}
        website_id = context.get('website_id', False)
        if website_id and isinstance(view_id, basestring):
            rec_id = self.search(cr, uid, [
                ('key', '=', view_id),
                ('website_id', '=', website_id),
            ], context=context)
            # if not rec_id:
            #     rec_id = self.search(cr, uid, [
            #         ('key', '=', view_id),
            #     ], context=context)
            if rec_id:
                _logger.info('_view_obj: (Website) Found as %s', rec_id)
                return self.browse(cr, uid, rec_id, context=context)[0]
            website = self.pool['website'].browse(cr, uid, website_id, context=context)
            theme_id = website.theme_id.id
            if theme_id:
                rec_id = self.search(cr, uid, [
                    ('key', '=', view_id),
                    ('theme_id', '=', theme_id),
                ], context=context)
                if rec_id:
                    _logger.info('_view_obj: (Theme) Found as %s', rec_id)
                    return self.browse(cr, uid, rec_id, context=context)[0]
        return super(view, self)._view_obj(cr, uid, view_id, context=context)

#    def _view_obj(self, cr, uid, view_id, context=None):
#        _logger.info('_view_obj: view_id = %s', view_id)
#        _logger.info('_view_obj: context = %s', context)
#        if isinstance(view_id, basestring):
#            try:
#                return self.pool['ir.model.data'].xmlid_to_object(
#                    cr, uid, view_id, raise_if_not_found=True, context=context
#                )
#            except:
#                _logger.info('_view_obj: Falling back')
#                # Try to fallback on key instead of xml_id
#                if self.search(cr, uid, [('key', '=', view_id),('website_id','=',context.get('website_id', False))], context=context):
#                    rec_id = self.search(cr, uid, [('key', '=', view_id),('website_id','=',context.get('website_id', False))], context=context)
#                else:
#                    rec_id = self.search(cr, uid, [('key', '=', view_id)], context=context)
#                if rec_id:
#                    return self.browse(cr, uid, rec_id, context=context)[0]
#                else:
#                    raise
#        elif isinstance(view_id, (int, long)):
#            return self.browse(cr, uid, view_id, context=context)
#
#        # assume it's already a view object (WTF?)
#        return view_id

    @tools.ormcache_context(accepted_keys=('website_id',))
    def get_view_id(self, cr, uid, xml_id, context=None):
        context = context or {}
        # _logger.info('get_view_id: xml_id = %s', xml_id)
        # _logger.info('get_view_id: context = %s', context)
        if context and 'website_id' in context and not isinstance(xml_id, (int, long)):
            domain = [
                ('key', '=', xml_id),
                '|',
                ('website_id', '=', context['website_id']),
                ('website_id', '=', False)
            ]
            xml_ids = self.search(cr, uid, domain, order='website_id', limit=1, context=context)
            if not xml_ids:
                xml_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, xml_id, raise_if_not_found=True)
                if self.read(cr, uid, xml_id, ['page'], context=context)['page']:
                    raise ValueError('Invalid template id: %r' % (xml_id,))
            else:
                xml_id = xml_ids[0]
        else:
            xml_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, xml_id, raise_if_not_found=True)
        return xml_id

    _read_template_cache = dict(accepted_keys=('lang', 'inherit_branding', 'editable', 'translatable', 'website_id'))

    @tools.ormcache_context(**_read_template_cache)
    def _read_template(self, cr, uid, view_id, context=None):
        # _logger.info('_read_template: view_id = %s', view_id)
        # _logger.info('_read_template: context = %s', context)
        arch = self.read_combined(cr, uid, view_id, fields=['arch'], context=context)['arch']
        arch_tree = etree.fromstring(arch)

        if 'lang' in context:
            arch_tree = self.translate_qweb(cr, uid, view_id, arch_tree, context['lang'], context)

        self.distribute_branding(arch_tree)
        root = etree.Element('templates')
        root.append(arch_tree)
        arch = etree.tostring(root, encoding='utf-8', xml_declaration=True)
        return arch

    @tools.ormcache(size=0)
    def read_template(self, cr, uid, xml_id, context=None):
        if isinstance(xml_id, (int, long)):
            view_id = xml_id
        else:
            if '.' not in xml_id:
                raise ValueError('Invalid template id: %r' % (xml_id,))
            view_id = self.get_view_id(cr, uid, xml_id, context=context)
        return self._read_template(cr, uid, view_id, context=context)

    def clear_cache(self):
        self._read_template.clear_cache(self)
        self.get_view_id.clear_cache(self)

    def get_inheriting_views_arch(self, cr, uid, view_id, model, context=None):
        _logger.info('get_inheriting_views_arch: view_id = %s', view_id)
        # _logger.info('get_inheriting_views_arch: model = %s', model)
        # _logger.info('get_inheriting_views_arch: context = %s', context)
        context = context or {}
        arch = super(view, self).get_inheriting_views_arch(cr, uid, view_id, model, context=context)
        if 'website_id' not in context:
            return arch

        website_id = context.get('website_id', False)
        website = self.pool['website'].browse(cr, uid, website_id, context=context)
        theme_id = False
        if website:
            theme_id = website.theme_id.id if website.theme_id else False
        view_ids = [vid for _, vid in arch]
        # Multi inherit: Add also views that inherit from this one via multi_inherit_ids
        multi_arch = self.pool['ir.ui.view.multi'].get_multi_inheriting_views_arch(
            cr, uid, view_id, context=context)
        for xml, vid in multi_arch:
            if vid not in view_ids:
                view_ids.append(vid)
                arch.append((xml, vid))
        # view_arch_to_add_per_key = {}
        keep_view_ids = []
        for view_rec in self.browse(cr, SUPERUSER_ID, view_ids, context):
            # Standard view
            if not (view_rec.website_id or view_rec.theme_id):
                _logger.info('get_inheriting_views_arch:    (%s) Standard view', view_rec.id)
                keep_view_ids.append(view_rec.id)
            # Theme view
            elif view_rec.theme_id and view_rec.theme_id.id == theme_id:
                _logger.info('get_inheriting_views_arch:    (%s) Theme view', view_rec.id)
                keep_view_ids.append(view_rec.id)
            # Website view
            elif view_rec.website_id and view_rec.website_id.id == website_id:
                _logger.info('get_inheriting_views_arch:    (%s) Website view', view_rec.id)
                keep_view_ids.append(view_rec.id)
            # Other ones will not apply

#            #case 1: there is no key, always keep the view
#            if not view_rec.key:
#                _logger.info('get_inheriting_views_arch: Case #1')
#                keep_view_ids.append(view_rec.id)
#            #case 2: Correct website
#            elif (view_rec.website_id and (
#                    view_rec.website_id.id == website_id or
#                    view_rec.theme_id.id == theme_id)):
#                _logger.info('get_inheriting_views_arch: Case #2')
#                view_arch_to_add_per_key[view_rec.key] = (view_rec.website_id.id, view_rec.id)
#            #case 3: no website add it if no website
#            if not view_rec.website_id:
#                _logger.info('get_inheriting_views_arch: Case #3')
#                view_web_id, view_id = view_arch_to_add_per_key.get(view_rec.key, (False, False))
#                if not view_web_id:
#                    view_arch_to_add_per_key[view_rec.key] = (False, view_rec.id)
#                #else: do nothing, you already have the right view
#            #case 4: website is wrong: do nothing
        #Put all the view_id we keep together
        #keep_view_ids.extend([view_id for _, view_id in view_arch_to_add_per_key.values()])
        res = [(xml, vid) for xml, vid in arch if vid in keep_view_ids]
        _logger.info('get_inheriting_views_arch: keep_view_ids = %s', keep_view_ids)
        return res
