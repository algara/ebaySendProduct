# -*- coding: utf-8 -*-
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError, ConnectionResponseError
from openerp.exceptions import RedirectWarning
import psycopg2




def get_values():  
    
    connection = None
    site='186'
    appid=None
    devid=None
    certid=None
    user_id=None
    ebay_token=None
    compatibility=None
    email=None
    database="nueva"
    host="localhost"
    user="odoo"
    list_users=[]
    existr=False
    exista=False
    sandbox=False
    try: 
        connection = psycopg2.connect(database='pfc',host="localhost" ,user='odoo',password="1234") 
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('(select * FROM information_schema.tables)')          
        rows = cursor.fetchall()
        for i in rows:
            if i[2]=="registration_objeto":
                existr=True
            if i[2]=="registration_sign_objeto":
                exista=True
        if existr:
            cursor.execute('SELECT * FROM registration_objeto ')          
            rows = cursor.fetchall()
            if len(rows)>0:
                ind=0
                for row in rows:
                  
                    site=row["site"]
                    appid=row["appid"]
                    devid=row["devid"]
                    certid=row["certid"]
                    list_users.append((row ["user_id"],row["site"])) 
                    ind+=1
                    compatibility=row["compatibility"]
                    sandbox=row["sandbox"]
        if exista:
            cursor.execute('SELECT * FROM registration_sign_objeto')
            res=cursor.fetchall()
            for a in list_users:
                for i in res:
                    
                    if i["user_id"]==a[0]:
                        ebay_token=i["eBay_Token"]
                        site=a[1]
                        print site
                    else:
                        print "TOKEN NO CARGADO"       
        
                   
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        raise RedirectWarning("queries.py: Problems in the configuration of data base:%s,host:%s,user:%s"%(database,host,user))
    finally:
        if connection:
            connection.close()
    
    list_countries=[]
    list_sites=[]
    list_currencies=[]
    list_paymentmethods=[]
    list_shipping=[]
    list_ShippingCostPaidByOption=[]
    list_ReturnsWithinOption=[]
    list_ReturnsAcceptedOption=[]
    
    #if sandbox:
    api = Trading(domain='api.sandbox.ebay.com',siteid=site)
    #else:
        #api=Trading(domain='api.ebay.com')
    if site and appid and devid and certid and compatibility:
        #Configure data to  trading correctly 
        print appid
        print devid
        print certid
        print compatibility
        print ebay_token
        api.config.set('siteid', site, force=True)
        api.config.set('compatibility', compatibility, force=True)
        api.config.set('appid', appid, force=True)
        api.config.set('devid', devid, force=True)
        api.config.set('certid', certid, force=True)
        
        if ebay_token:
            api.config.set('token', ebay_token, force=True)
    
    try:
        
            response=api.execute('GeteBayDetails')
    except ConnectionError as e:
        raise RedirectWarning("Error connect to eBay.\n %s"%e.message) 
    except ConnectionResponseError as e:
        raise RedirectWarning("Error response to eBay.\n %s"%e.message)
            
    else:
        #Calculate list of sites available
        sites=(response.dict().get('SiteDetails'))
        num_sites=len(sites)   
        i=0
        while i<num_sites:
            list_sites.append((sites[i].get('SiteID'),sites[i].get('Site')))
            i+=1
            
        #Calculate list of currencies available
        currencyDetails=response.dict().get('CurrencyDetails')
        num_currency=len(currencyDetails)   
        i=0
        while i<num_currency:  
            list_currencies.append((currencyDetails[i].get('Currency'),currencyDetails[i].get('Description')))
            i+=1
        
        countries=(response.dict().get('CountryDetails'))
        num_countries=len(countries)
        i=0
        
        #Calculate list of countries available
        while i<num_countries:
            list_countries.append((countries[i].get('Country'),countries[i].get('Description')))
            i+=1 
        
        return_accepted=response.dict().get("ReturnPolicyDetails").get("ReturnsAccepted")
        num=len(return_accepted)
        i=0
        list_ReturnsAcceptedOption=[]
        while i<num:
            list_ReturnsAcceptedOption.append((return_accepted[i].get("ReturnsAcceptedOption"),return_accepted[i].get("Description")))
            i+=1  
          
        paymentOptionDetails=response.dict().get('PaymentOptionDetails')
        num_payment=len(paymentOptionDetails)
        i=0
        while i<num_payment:
                    
            list_paymentmethods.append((paymentOptionDetails[i].get('PaymentOption'),paymentOptionDetails[i].get('Description')))
            i+=1
                
            
        shippingServiceDetails=response.dict().get('ShippingServiceDetails')
        num_shippingservice= len(shippingServiceDetails)
        i=0 
        while i< num_shippingservice:
            if shippingServiceDetails[i].get("ValidForSellingFlow")=="true":
             
                list_shipping.append((shippingServiceDetails[i].get('ShippingService'),shippingServiceDetails[i].get('Description')))
            i+=1
             
             
        who_pay=response.dict().get("ReturnPolicyDetails").get("ShippingCostPaidBy")
        num=len(who_pay)
        i=0
        list_ShippingCostPaidByOption=[]
        while i<num:
            list_ShippingCostPaidByOption.append((who_pay[i].get("ShippingCostPaidByOption"),who_pay[i].get("Description")))
            i+=1
            

        whitin=response.dict().get("ReturnPolicyDetails").get("ReturnsWithin")
        num=len(whitin)
        i=0
        list_ReturnsWithinOption=[]
        while i<num:
            list_ReturnsWithinOption.append((whitin[i].get("ReturnsWithinOption"),whitin[i].get("Description")))
            i+=1
          
    
            
    
    
    return list_countries,list_sites,list_currencies,list_paymentmethods,list_shipping,site,email,list_ShippingCostPaidByOption,list_ReturnsWithinOption,list_ReturnsAcceptedOption

