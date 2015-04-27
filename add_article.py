# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError, ConnectionResponseError
from queries import get_values 
from datetime import datetime
import base64

from openerp import tools
from openerp.exceptions import RedirectWarning

class add_article(models.Model):
    _name = 'add_article.objeto'
    
    lists=[[],[],[],[],[],None,None]
    
    lists=get_values()
   
    id_site=lists[5]
    print "El sitio que carga es:",id_site
    id_email=lists[6]
    
    imagen= fields.Binary(string="Image",translate=True)
    
    product_id= fields.Many2one('product.product', 'Product', required=True, ondelete='no action')
    
    country= fields.Selection(selection=lists[0],string="Country",help="Choose your country",required=True,translate=True) 
    #location=fields.Selection(selection=,string="Location",help="The geographical location of the item")
    postalCode=fields.Integer(string='Postal Code',translate=True,required=True,help="http://www.upu.int/en/resources/postcodes/looking-up-a-postcode/list-of-sites-by-country.html")           
    
    site=fields.Selection(selection=lists[1],string="Site of Sale",required=True,help="Your Sale`s Site",default=id_site,translate=True)
    
    currency= fields.Selection(selection=lists[2],string='Currency', required=True,help="Currency of sale's site",translate=True)
    
    paymentMethods=fields.Selection(selection=lists[3],string='Payment Method',required=True,translate=True)
    actual_state=fields.Boolean(string="actual_state",default=False) 
    
    
    category=fields.Selection(selection="_get_categories",string="Category",required=True,help="Primary Category",translate=True)
    send_category=fields.Integer(string="eBay Category", required=True,help="Select the number of leaf category http://www.sandbox.ebay.com/",default=3179,translate=True)
    enl_cat=fields.Char(string="URL Category",default="http://cgi5.sandbox.ebay.es/ws/eBayISAPI.dll?NewListing",readonly=True)
    start_date= fields.Date(string='Start Date',help="Date since you want selling your product",translate=True)
    
    title=fields.Char(string='Title of product',help="Title to make your product  appealing",required=True,translate=True)
   
    conditionID=fields.Selection(selection="_condition",string='Condition of product',required=True,translate=True)
    
    pictureDetails= fields.Char(string='URL Picture',help="A ,http:// or ftp:// ,link",translate=True)
    tinypic=fields.Char(string="Click to get upload picture",default="http://es.tinypic.com/",readonly=True,translate=True)
    description_article=fields.Text(string="Description",help="Write a short description of your product",translate=True)
    
    listingDuration=fields.Selection(selection='_listing',string='Number of days',required=True,translate=True)
    
    startPrice=fields.Float(string='Start Price',required=True,default=1.0,help="Price >=1.0",translate=True)
    #Policy
    shippingServiceCost=fields.Float(string="Shipping Service Cost",required=True,help="Cost of shipping service",translate=True)
    shippingservice=fields.Selection(selection=lists[4],string="Shipping Service",help='Choose Shipping Service Available',required=True,translate=True)
    who_pay=fields.Selection(selection=lists[7],string='ShippingCostPaidBy', help="Who pays the cost of shipping",translate=True)
    whitin=fields.Selection(selection=lists[8],string='ReturnsWithin', help="Number of Days to return without cost",translate=True)
    return_accepted=fields.Selection(selection=lists[9],string='Refund', required=True,help="If are accepted returns",default="ReturnsNotAccepted",translate=True)
    #Update
    cost=fields.Float(string="Cost of Update")
    foot=fields.Selection(selection=[("ini","ini"),("env","env")],string="Foot",default='ini')
    item_id= fields.Char(string='Article ID',readonly=True,help="ID of product",translate=True)
    url_id= fields.Char(string='Article URL',readonly=True,help="URL of product",translate=True)
    
    @api.onchange('product_id')
    def add_price(self):
        
        if not self.env.context.has_key("check_view_ids"):
            bb=self.pool.get('product.template').search_read(self.env.cr, self.env.context["uid"])
            for i in bb:
                if i["id"]==self.product_id.id:
                    self.startPrice=i["list_price"]
                    self.imagen=i["image"]
                    self.description_article=i["description_sale"]
                    break;
        if not self.env.context.has_key("check_view_ids"):
            bb=self.pool.get('product.product').search_read(self.env.cr, self.env.context["uid"])
            for i in bb:
                if i["id"]==self.product_id.id:
                    self.pictureDetails=i["default_code"]
                    break;
    def _listing(self):
        list=[]
        if self.id_site=="186":
            list=[
                  ("Days_3","3 días"),
                  ('Days_5',"5 días"),
                  ("Days_7","7 días"),
                  ("Days_10","10 días")]
        else:
            list=[
                  ("Days_3","3 days"),
                  ('Days_5',"5 days"),
                  ("Days_7","7 days"),
                  ("Days_10","10 days")]
        return list
    def _condition(self):
        list=[]
        
        if self.id_site=="186":  
            list=[('1000','Nuevo'),
                                  ('1500','Nuevo (Sin empaquetar)'),
                                  ('1750','Nuevo (con defectos de fabricación)'),
                                  ('2000','Restaurado en Fábrica'),
                                  ('2500','Restaurado por el vendedor'),
                                  ('3000','Usado'),
                                  ('4000','Usado (Muy buenas condiciones)'),
                                  ('5000','Usado (Buenas condiciones)'),
                                  ('6000','Usado (Aceptables condiciones)'),
                                  ('7000','Por partes o no funciona')]
        else:
            list=[('1000','New'),
                                  ('1500','New other (see details)'),
                                  ('1750','New with defects'),
                                  ('2000','Manufacturer refurbished'),
                                  ('2500','Seller refurbished'),
                                  ('3000','Used'),
                                  ('4000','Very Good'),
                                  ('5000','Good'),
                                  ('6000','Acceptable'),
                                  ('7000','For parts or not working')]
                                    
        return list    


    def verify_update_product(self,cr,uid,ids,context=None):
        user=self.browse(cr, uid,ids, context)
        if not user.pictureDetails:
            user.pictureDetails="http://i61.tinypic.com/2qbhqtt.jpg"
        if user.return_accepted=="ReturnsNotAccepted":
            Data={
                  "Item":{
                       #http://developer.ebay.com/devzone/xml/docs/Reference/ebay/types/CountryCodeType.html
                      "Country":user.country,
                      "PostalCode":user.postalCode,
                      "currency":user.currency,
                      "PaymentMethods":user.paymentMethods,
                      "ShippingDetails": {
                                          
                                          "ShippingServiceOptions": {
                                                                     "ShippingService": user.shippingservice,
                                                                     "ShippingServiceCost":user.shippingServiceCost
                                                                     }
                                          },
                      "PrimaryCategory":{"CategoryID":user.send_category},#45454
                      #"start_date":user.start_date,
                      "PictureDetails":{"PictureURL": user.pictureDetails},
                      "Description":user.description_article,
                      "ListingDuration":user.listingDuration,
                      "StartPrice":user.startPrice,
                      "Title":user.title,
                      "ConditionID":user.conditionID,
                      "CategoryMappingAllowed": "true",
                      "DispatchTimeMax":"5",
                      "ReturnPolicy": {
                            "ReturnsAcceptedOption": user.return_accepted,
                        }
                      }
                }
        else:
            Data={
                  "Item":{
                       #http://developer.ebay.com/devzone/xml/docs/Reference/ebay/types/CountryCodeType.html
                      "Country":user.country,
                      "PostalCode":user.postalCode,
                      "currency":user.currency,
                      "PaymentMethods":user.paymentMethods,
                      "ShippingDetails": {
                                          
                                          "ShippingServiceOptions": {
                                                                     "ShippingService": user.shippingservice,
                                                                     "ShippingServiceCost":user.shippingServiceCost
                                                                     }
                                          },
                      "PrimaryCategory":{"CategoryID":user.send_category},
                      #"start_date":user.start_date,
                      "PictureDetails":{"PictureURL": user.pictureDetails},
                      "Description":user.description_article,
                      "ListingDuration":user.listingDuration,
                      "StartPrice":user.startPrice,
                      "Title":user.title,
                      "ConditionID":user.conditionID,
                      "CategoryMappingAllowed": "true",
                      "DispatchTimeMax":"5",
                      "ReturnPolicy": {
                            "ReturnsAcceptedOption": user.return_accepted,
                            "ReturnsWithinOption": user.whitin,
                            "Description": "If you are not satisfied, return the product for refund.",
                            "ShippingCostPaidByOption":user.who_pay
                        }
                      }
                }
        print user.category
        bb=self.pool.get('registration.objeto').search_read(cr, uid)
        for i in bb:
            user_registered_correct_session=False
            token=""
            active_sessions= self.pool.get('registration_sign.objeto').search_read(cr,uid)#List of users read[]
            for ses in active_sessions:
                if ses["eBay_Token"]and ses["actual_state"]=="inside":
                    
                    timestamp=ses["hour_session"]
                    hour=datetime.now()
                    hour_seg=int(hour.strftime('%s'))
                    
                    tim=hour_seg-timestamp
                    if tim<1200:#If it has not passed more than 1200 seconds, validate session 
                        print "TIME",tim
                        user_registered_correct_session=True
                        token=ses["eBay_Token"]
                        break
                    else:
                        ses["user_id"]="INVALID"
                        action_id=self.pool['ir.model.data'].get_object_reference(cr,uid,'ebaypasoapaso','registration_sign_objeto_action')
                        raise RedirectWarning("Invalid Session. You have to delete your session and come back to SIGN IN",action_id[1],"Go to create another one")
                        print "INVALID SESSION, You have to come back to SIGN IN"
            if uid==i["create_uid"][0] and user_registered_correct_session:#User has account and is registered, and he has correct session
                api = Trading(domain='api.sandbox.ebay.com')
                site=i["site"]
                appid=i["appid"]
                devid=i["devid"]
                certid=i["certid"]
                if  site and appid and devid and certid:
                    
                    api.config.set('siteid', site, force=True)
                    api.config.set('appid', appid, force=True)
                    api.config.set('devid', devid, force=True)
                    api.config.set('certid', certid, force=True)
                    api.config.set("token",token,force=True)
                    
                    try:
                        response = api.execute('VerifyAddItem',Data)
                    except ConnectionError as e:
                        print(e)
                        print(e.response.dict())
                        raise RedirectWarning("Error verifying Add Item on eBay, Try it again.\nERROR:%s"%e.message)
                    except ConnectionResponseError as e:
                            raise RedirectWarning("Error response verifying Add Item session token to eBay.\n %s"%e.message)
                    
                    
                    else:
                        if response.dict().get("ItemID")=='0':
                            print "ITEM VERIFICADO"
                            cost=0
                            fee=response.dict().get("Fees").get("Fee")
    
                            i=0
                            while i<len(fee):
                                cost+=float( fee[i].get("Fee").get("value"))
                                i+=1
                            self.write(cr,uid,ids,{
                                                   #"actual_state":True,
                                                   "cost":cost,
                                                   "foot":"env"},context=context)
                            return {
                                    'name': "Send Product",
                                    'type': 'ir.actions.act_window',
                                    'res_model': 'add_article.objeto',
                                    'view_mode': 'form',
                                    'view_type': 'form',
                                    'res_id': user.id,
                                    'views': [(False, 'form')],
                                    'target': 'new'
                                    
                                    }
                            print "If you are not using a sandbox account, this update will have a cost of", cost
                            
                        else: 
                            print "ITEM INCORRECTO"
                    
            elif uid==i["create_uid"][0]:#If user has not initiated session
                print "User has not initiated session or Session is out of date, it is necessary you initiate it"
                return {
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'registration_sign.objeto',
                        }
                
            elif user_registered_correct_session:#If actual user does not have account registered
                print "Actual user does not have account registered, Create it"                        
                return {
                        'name': "New eBay User Authentication",
                        'type': 'ir.actions.act_window',
                        'res_model': 'registration.objeto',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'views': [(False, 'form')],
                        'target': 'new',
                        }
            
       
        
    
    def update_product(self,cr,uid,ids,context):
        user=self.browse(cr, uid,ids, context)
        if not user.pictureDetails:
            user.pictureDetails="http://i61.tinypic.com/2qbhqtt.jpg"
        if user.return_accepted=="ReturnsNotAccepted":
            Data={
                  "Item":{
                       #http://developer.ebay.com/devzone/xml/docs/Reference/ebay/types/CountryCodeType.html
                      "Country":user.country,
                      "PostalCode":user.postalCode,
                      "currency":user.currency,
                      "PaymentMethods":user.paymentMethods,
                      "ShippingDetails": {
                                          
                                          "ShippingServiceOptions": {
                                                                     "ShippingService": user.shippingservice,
                                                                     "ShippingServiceCost":user.shippingServiceCost
                                                                     }
                                          },
                      "PrimaryCategory":{"CategoryID":user.send_category},#45454
                      #"start_date":user.start_date,
                      "PictureDetails":{"PictureURL": user.pictureDetails},
                      "Description":user.description_article,
                      "ListingDuration":user.listingDuration,
                      "StartPrice":user.startPrice,
                      "Title":user.title,
                      "ConditionID":user.conditionID,
                      "CategoryMappingAllowed": "true",
                      "DispatchTimeMax":"5",
                      "ReturnPolicy": {
                            "ReturnsAcceptedOption": user.return_accepted,
                        }
                      }
                }
        else:
            Data={
                  "Item":{
                       #http://developer.ebay.com/devzone/xml/docs/Reference/ebay/types/CountryCodeType.html
                      "Country":user.country,
                      "PostalCode":user.postalCode,
                      "currency":user.currency,
                      "PaymentMethods":user.paymentMethods,
                      "ShippingDetails": {
                                          
                                          "ShippingServiceOptions": {
                                                                     "ShippingService": user.shippingservice,
                                                                     "ShippingServiceCost":user.shippingServiceCost
                                                                     }
                                          },
                      "PrimaryCategory":{"CategoryID":user.send_category},
                      #"start_date":user.start_date,
                      "PictureDetails":{"PictureURL": user.pictureDetails},
                      "Description":user.description_article,
                      "ListingDuration":user.listingDuration,
                      "StartPrice":user.startPrice,
                      "Title":user.title,
                      "ConditionID":user.conditionID,
                      "CategoryMappingAllowed": "true",
                      "DispatchTimeMax":"5",
                      "ReturnPolicy": {
                            "ReturnsAcceptedOption": user.return_accepted,
                            "ReturnsWithinOption": user.whitin,
                            "Description": "If you are not satisfied, return the product for refund.",
                            "ShippingCostPaidByOption":user.who_pay
                        }
                      }
                }
        print user.category
        bb=self.pool.get('registration.objeto').search_read(cr, uid)
        for i in bb:
            user_registered_correct_session=False
            token=""
            active_sessions= self.pool.get('registration_sign.objeto').search_read(cr,uid)#List of users read[]
            for ses in active_sessions:
                if ses["eBay_Token"]and ses["actual_state"]=="inside":
                    
                    timestamp=ses["hour_session"]
                    hour=datetime.now()
                    hour_seg=int(hour.strftime('%s'))
                    
                    tim=hour_seg-timestamp
                    if tim<1200:#If it has not passed more than 1200 seconds, validate session 
                        print "TIME",tim
                        user_registered_correct_session=True
                        token=ses["eBay_Token"]
                        break
                    else:
                        
                        print "INVALID SESSION, You have to come back to SIGN IN"
            if uid==i["create_uid"][0] and user_registered_correct_session:#User has account and is registered, and he has correct session
                api = Trading(domain='api.sandbox.ebay.com')
                site=i["site"]
                appid=i["appid"]
                devid=i["devid"]
                certid=i["certid"]
                if  site and appid and devid and certid and token:
                    
                    api.config.set('siteid', site, force=True)
                    api.config.set('appid', appid, force=True)
                    api.config.set('devid', devid, force=True)
                    api.config.set('certid', certid, force=True)
                    api.config.set("token",token,force=True)
                    
                    try:
                        response = api.execute('AddItem',Data)
                    except ConnectionError as e:
                        print(e)
                        print(e.response.dict())
                        raise RedirectWarning("Error to Add Item on eBay, Try it again.\nERROR:%s"%e.message)
                    except ConnectionResponseError as e:
                            raise RedirectWarning("Error response adding item to eBay.\n %s"%e.message)
                    else:
                    
                        if response.dict().get("ItemID"):
                            print "ITEM VERIFICADO"
                            
                            name=response.dict().get("ItemID")
                            url="http://cgi.sandbox.ebay.es/%s"%name
                            cost=0
                            fee=response.dict().get("Fees").get("Fee")
    
                            i=0
                            while i<len(fee):
                                cost+=float( fee[i].get("Fee").get("value"))
                                i+=1
                            
                            self.write(cr,uid,ids,{
                                                   "country":user.country,
                                                   "postalCode":user.postalCode,
                                                   "site":user.site,
                                                   "currency":user.currency,
                                                   "paymentMethods":user.paymentMethods,
                                                   "category":user.category,
                                                   "send_category":user.send_category,
                                                   "start_date":user.start_date,
                                                   "title":user.title,
                                                   "conditionID":user.conditionID,
                                                   "pictureDetails":user.pictureDetails,
                                                   "description_article":user.description_article,
                                                   "listingDuration":user.listingDuration,
                                                   "start_Price":user.startPrice,
                                                   "shippingServiceCost":user.shippingServiceCost,
                                                   "shippingservice":user.shippingservice,
                                                   "who_pay":user.who_pay,
                                                   "whitin":user.whitin,
                                                   "return_accepted":user.return_accepted,
                                                   "item_id":name,
                                                   "url_id":url,
                                                   
    
                                                   "actual_state":True,
                                                   "cost":cost,
                                                   "foot":"env"},context=context)
                            return {
                                    'type': 'ir.actions.act_window',
                                    'view_mode': 'tree,form',
                                    'view_type': 'form',
                                    'res_model': 'add_article.objeto',
                                    
                                    }
                            print "If you are not using a sandbox account, this update  has had a cost of", cost
                            raise RedirectWarning("If you are not using a sandbox account, this update  has had a cost of", cost)
                        else: 
                            print "ITEM INCORRECTO"
                            
                    
            elif uid==i["create_uid"][0]:#If user has not initiated session
                print "User has not initiated session or Session is out of date, it is necessary you initiate it"
                return {
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'registration_sign.objeto',
                        }
                
            elif user_registered_correct_session:#If actual user does not have account registered
                print "Actual user does not have account registered, Create it"                        
                return {
                        'name': "New eBay User Authentication",
                        'type': 'ir.actions.act_window',
                        'res_model': 'registration.objeto',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'views': [(False, 'form')],
                        'target': 'new',
                        }
        
        print "UPDATED"
        
    def _get_categories(self):  
        list_categories=[]              
        bb=self.env['registration.objeto'].search_read()
        if len(bb)==0:
            if not self.env.context.has_key("check_view_ids"):
                action_id=self.pool['ir.model.data'].get_object_reference(self.env.cr,self.env.context["uid"],'ebaypasoapaso','join_authorize')
                raise RedirectWarning("There is not anyone user register",action_id[1],"Go to create it")
            
        for i in bb:            
               
                     
            #Check if we are upgrading the module, because if not we have a execution fail, because CONTEXTS are different
              
            if self.env.context.has_key("check_view_ids"):
                return list_categories
            else:
                #If user that is surfing, is registered and his session is active
                user_registered=False
                active_sessions=self.env['registration_sign.objeto'].search_read()
                for ses in active_sessions:
                    if ses["eBay_Token"]and ses["actual_state"]=="inside":
                        user_registered=True
                    
                if(self.env.context["uid"]==i["create_uid"][0])and(user_registered):
                    #list_categories=get_categories(i["site"])
                    Data = {            
                        #http://developer.ebay.com/devzone/shopping/docs/callref/types/SiteCodeType.html
                        #'CategorySiteID': site,            
                        #Specifies the maximum depth of the category hierarchy to retrieve, where the top-level categories (meta-categories) are at level 1
                        'LevelLimit': 1,#Default=0
                        'ViewAllNodes':True,
                        'DetailLevel': 'ReturnAll',
                        #'ErrorLanguage':'en_US'#en_US United States, es_ES Spain
                    }
                
                    api = Trading(domain='api.sandbox.ebay.com')
                    site=i["site"]
                    appid=i["appid"]
                    devid=i["devid"]
                    certid=i["certid"]
                    if  site and appid and devid and certid:
                        api.config.set('siteid', site, force=True)
                        api.config.set('appid', appid, force=True)
                        api.config.set('devid', devid, force=True)
                        api.config.set('certid', certid, force=True)
                        
                        try:
                            response = api.execute('GetCategories',Data)
                        except ConnectionError as e:
                            print(e)
                            print(e.response.dict())
                            raise RedirectWarning("Error to get categories on eBay, Try it again.\nERROR:%s"%e.message)
                        except ConnectionResponseError as e:
                            raise RedirectWarning("Error response getting categories token to eBay.\n %s"%e.message)
                        else:
                            d=[]
                            d=response.reply.get('CategoryArray').get('Category')
                            num=0
                            num=int(response.reply.get('CategoryCount'))
                            i=0                
                            while (i<num):
                                list_categories.append((d[i].get('CategoryID'),d[i].get('CategoryName')))
                                i=i+1  
                                              
                else:
                    
                    raise RedirectWarning("You have not got account user or You have not got session initiated")
                    print"GET CATEGORIES:EL UID ACTUAL NO TIENE CUENTA, O NO TIENE SESIÓN INICIADA, COMPRUÉBELO"
                    
                return list_categories
    
   
    @api.onchange('site')
    def check_change(self):
        if self.site=="15":
            self.currency="AUD"                       
        elif self.site=="210"  or self.site=="2":
            self.currency= "CAD"
        elif self.site=="193":
            self.currency= "CHF"
        elif self.site=="77" or self.site=="71"or self.site=="101" or self.site=="146" or self.site=="186" or self.site=="123"or self.site=="23" or self.site=="16" or self.site=="205":
            self.currency= "EUR"
        elif self.site=="3":
            self.currency= "GBP"
        elif self.site=="201":
            self.currency= "HKD"
        elif self.site=="203":
            self.currency= "INR"
        elif self.site=="207":
            self.currency= "MYR"
        elif self.site=="211":
            self.currency= "PHP"
        elif self.site=="212":
            self.currency= "PLN"
        elif self.site=="218":
            self.currency= "SEK"
        elif self.site=="216":
            self.currency= "SGD"
        elif self.site=="0"or self.site=="100":
            self.currency= "USD"
        else:
            self.currency=False
            """            
            print"\n\n"
            print "USER:",self.env.user
            print "CR:",self.env.cr
            print "CONTEXT:",self.env.context
            print "ENV:",self.env
            print "LEIDO=",self.search_read([("country","!=","185")])
            bb=self.env['registration.objeto'].search_read()
            print "ESTO ES BB:",bb
            for i in bb:
                if(self.env.context["uid"]==i["create_uid"][0]):
                    print "El creador es el mismo que esta navegando"
                    print "EMAIL:",i["email"]
                    print "APPID:",i["appid"]
                    print "CERTID:",i["certid"]
                    print "DEVID:",i["devid"]
                    #print "USER_TOKEN:",i["user_token"]
                    print "CREADOR:",i["create_uid"][0]
                    print "CREADOR:",i["create_uid"][1]
                    print "THIS:"
            """
            #print "UID del usuario: ",self.env.context["uid"]
            #print self.search_read([("country","!=","185")])
            #d1= self.search_read([("country","!=","185")])[0]
            #d2=self.search_read([("country","!=","185")])[1]
            #print "\nD1",d1
            #print "\nD2",d2,"\n"
           
       
    
