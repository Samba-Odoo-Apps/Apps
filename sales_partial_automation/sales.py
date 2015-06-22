from openerp import models,fields, api, netsvc
import logging
from contextlib import contextmanager

_logger = logging.getLogger(__name__)
@contextmanager
def commit(cr):
    """
    Commit the cursor after the ``yield``, or rollback it if an
    exception occurs.

    Warning: using this method, the exceptions are logged then discarded.
    """
    try:
        yield
    except Exception:
        cr.rollback()
        _logger.exception('Error during an automatic workflow action.')
    else:
        cr.commit()


class sale(models.Model):
    _inherit="sale.order"
    load_purchase_batch=fields.Char('Load purchase batch')
    storecredit=fields.Char('store credit')
    invoice_ref=fields.Char('Invoice Number')
    invoice_date=fields.Date('Invoice Date')
    

    def _validate_sale_orders(self,cr,uid,sale_id):
        sale_obj = self.pool.get('sale.order')
        sale= sale_obj.browse(cr,uid,sale_id)
        sale.action_button_confirm()
        cr.commit()
        
        
    def _validate_invoices(self,cr,uid,sale_id,context=None):
        wf_service = netsvc.LocalService("workflow")
        sale_obj=self.pool.get('sale.order')
        sale_browse=sale_obj.browse(cr,uid,sale_id)
        invoice_id=sale_obj.action_invoice_create(cr,uid,[sale_id])
        invoice_obj = self.pool.get('account.invoice')
        invoice_obj = self.pool.get('account.invoice')
        try:
            with commit(cr):
                wf_service.trg_validate(uid, 'account.invoice',
                                                invoice_id, 'invoice_open', cr)
            invoice_obj.write(cr,uid,[invoice_id],{'comment':"Validated by sale done button"})
        except:
            invoice_obj.write(cr,uid,[invoice_id],{'comment':"wrong: somthing wrong with product configuration thats why unable to confirm"})


    
    def _validate_pickings(self,cr,uid,sale_id):
        sale_obj=self.pool.get('sale.order')
        sale_browse=sale_obj.browse(cr,uid,sale_id)
        picking_obj = self.pool.get('stock.picking')
        picking_id = picking_obj.search(cr,uid,[('origin','=',sale_browse.name)])
        if picking_id:
            try:
                picking_obj.action_assign(cr,uid,picking_id)
                picking_obj.force_assign(cr,uid,picking_id)
                picking_obj.action_done(cr,uid,picking_id)
            except:
                sale_obj.write(cr,uid,[sale_id],{'note':' wrong: something wrong with your order please check once orderline configuration product, delivery not done!'})

        else:
            sale_obj.write(cr,uid,[sale_id],{'note':' wrong: something wrong with your order please check once orderline configuration product, delivery not done!'})


    def inv_del(self,cr,uid,ids,context=None):
        sale_id=ids[0]
        self._validate_sale_orders(cr,uid,sale_id)
        self._validate_invoices(cr,uid,sale_id)
        self._validate_pickings(cr,uid,sale_id)
        return True
        
        #self._validate_pickings(cr, uid, sale_ids, context=context)
        