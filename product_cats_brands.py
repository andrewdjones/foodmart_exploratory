########################################
#Code base for Foodmart recommendations
#csv datasets from https://sites.google.com/a/
#dlpage.phi-integration.com/pentaho/mondrian/mysql-foodmart-database/foodmart_mysql.tar.gz
#
#This python file contains functions for looking up and labeling data (section 1)
#Calculating hierarchical children and revenues (section 2)
#Plotting simple visualizations for brands and product groupings (section 3)
#
#Andrew Jones
#andrew.d.jones@yale.edu
#July 2016
########################################
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from foodmart_mysql_explo import *
import collections
import operator
from decimal import Decimal
from string import strip, Template

########################################
# Labeling
########################################
def productClassName(pc_id):
    '''
    Returns product_subcategory name for product_class_id pc_id
    '''
    product_class_lookups = {}
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT product_subcategory FROM product_class WHERE product_class_id = "+str(pc_id)
    cursor.execute(query)
    allProds = cursor.fetchall()
    return allProds[0][0].strip('u()"')

def productClassLookups(mode = 'class_id'):
    '''
    If mode == class_id: Returns dict {product_id: associated product_class_id)}
    If mode == brand: dict {product_id: [product_class_id,associated brand_name]}
    '''
    product_id_lookups = {}
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    if mode == 'class_id':
        query = "SELECT product_class_id, product_id FROM product"
        cursor.execute(query)
        allProds = cursor.fetchall()
        #product_class_id hashed by product_id
        for p_class, p_id in allProds:
            product_id_lookups[p_id] = p_class
    elif mode == 'brand':
        query = "SELECT product_class_id, brand_name, product_id FROM product"
        cursor.execute(query)
        allProds = cursor.fetchall()
        #[product_class_id,brand_name] hashed by product_id
        for p_class, p_brand, p_id in allProds:
            product_id_lookups[p_id] = [p_class,p_brand]
    return product_id_lookups

def productCategoryLookups():
    '''
    Returns dict {product_class_id: [product_category, product_dept, product_fam]}
    '''
    product_class_lookups = {}
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT product_class_id, product_category, product_department, product_family FROM product_class"
    cursor.execute(query)
    allProds = cursor.fetchall()
    for p_data in allProds:
        product_class_lookups[p_data[0]] = p_data[1:]
    #for dictionary values, index (0,1,2) will get (category, department, family)
    return product_class_lookups

########################################
# Calculating
########################################
def getChildren(hier,nm):
    '''
    For group name n at hierarchy 
    lev = [family,department,category,product_class_id,brand].index(hier)
    Returns list of children in level (lev+1)
    '''
    tree = ['product_family','product_department','product_category','product_class_id','brand']
    lev = tree.index(hier)
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    #pull distinct subgroups at next hierarchical level
    queryTemp = Template("SELECT DISTINCT $m FROM product_class WHERE $l = $n")
    query = queryTemp.substitute(m = tree[lev+1], l = hier, n = nm)
    cursor.execute(query)
    lev_children = []
    for x in cursor.fetchall():
        #make a clean list of the children
        if type(x[0]) == int:
            lev_children.append(x[0])
        else:
            lev_children.append(strip(x[0],'u()"'))
    #print lev_children
    return lev_children

def revByGroup(hier):
    '''
    hier in ('product_class_id',product_category','product_department','product_family') 
    returns dict {hier:[store_sales,store_cost]}
    '''
    #get product_id to class lookups, hashed by product_id
    product_id_lookups = productClassLookups(mode = "class_id")
    #get the product class to category lookups, hashed by product_class
    product_cat_lookups = productCategoryLookups()
    #link dicts to get lookup from product_id to category, department, or family
    product_class_lookups = {}
    for p_id,p_class in product_id_lookups.items():
        if hier=='product_class_id':
            product_class_lookups[p_id] = p_class
        if hier=='product_category':
            product_class_lookups[p_id] = product_cat_lookups[p_class][0]
        elif hier=='product_department':
            product_class_lookups[p_id] = product_cat_lookups[p_class][1]
        elif hier=='product_family':
            product_class_lookups[p_id] = product_cat_lookups[p_class][2]
        else:
            raise NameError('Check requested lookup hierarchy')
    
    #pull transaction data in form (product_id, store_sales)    
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT product_id, store_sales, store_cost FROM transactions_rev"
    cursor.execute(query)
    trans_data = cursor.fetchall()
    
    #add all sales data to the hier relevant to product_id
    hierRev,hierCost = collections.Counter(),collections.Counter()
    for id,sales,cost in trans_data:
        hierRev[product_class_lookups[id]] += sales 
        hierCost[product_class_lookups[id]] += cost
    outDict = {key:[hierRev[key],hierCost[key]] for key in hierRev.keys()}
    #print outDict
    return outDict

def revByTwoGroups(g1,g2):
    '''
    g1 = (hier1,name1); g2 = (hier2,name2)
    hier in ['product_family','product_department','product_category','product_class_id']
    returns [store_sales,store_cost] for all product_id transactions in both g1 and g2
    '''
    #get product_id to class lookups, hashed by product_id
    product_id_lookups = productClassLookups(mode = "class_id")
    #get the product class to category lookups, hashed by product_class
    product_cat_lookups = productCategoryLookups()
    #link dicts to get lookup from product_id to category, department, or family
    product_class_lookups = [{},{}]
    #hierarchical levels of the two groups
    hiers = [g1[0],g2[0]]
    #order the hierarchical lookup dicts based on the two requested hiers
    for p_id,p_class in product_id_lookups.items():
        if 'product_class_id' in hiers:
            product_class_lookups[hiers.index('product_class_id')][p_id] = p_class
        if 'product_category' in hiers:
            product_class_lookups[hiers.index('product_category')][p_id] = product_cat_lookups[p_class][0]
        if 'product_department' in hiers:
            product_class_lookups[hiers.index('product_department')][p_id] = product_cat_lookups[p_class][1]
        if 'product_family' in hiers:
            product_class_lookups[hiers.index('product_family')][p_id] = product_cat_lookups[p_class][2]
    
    #pull transaction data in form (product_id, store_sales)    
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT product_id, store_sales, store_cost FROM transactions_rev"
    cursor.execute(query)
    trans_data = cursor.fetchall()
    
    #add all sales data to the hier relevant to product_id
    hierRev,hierCost = Decimal(0.0),Decimal(0.0)
    for id,sales,cost in trans_data:
        if product_class_lookups[0][id] == g1[1] and product_class_lookups[1][id] == g2[1]:
            hierRev += sales 
            hierCost += cost
    #print [hierRev,hierCost]
    return [hierRev,hierCost]

def revenueByQuarter(mode = 'categories',stores = 'all',track='store_sales'):
    '''
    Returns a dict hashed by quarter (1-4), where each entry is a Counter
    if mode == brands: Counter tallies quarterly store sales by brand
    if mode == categories: Counter tallies quarterly store sales by product_category
    if type(stores) == int, pulls quarterly revenue for that particular store_id
    if stores != 'all' and type(stores) != int, tallies quarterly revenue per store,
    outputs a more complicated dict {quarter: {store: {category : sales}}}
    track should be in ('store_sales','store_sales,store_cost')
    '''
    if mode=='categories':
        #get product_id to class lookups, hashed by product_id
        product_id_lookups = productClassLookups(mode = "class_id")
        #get the product class to category lookups, hashed by product_class
        product_cat_lookups = productCategoryLookups()
        #link dicts to get lookup from product_id to category
        product_class_lookups = {}
        for p_id,p_class in product_id_lookups.items():
            product_class_lookups[p_id] = product_cat_lookups[p_class][0]
    elif mode=='brands':
        #get the product_id to [product_class_id,brand_name] lookups
        product_class_lookups= productClassLookups(mode = 'brand')
    
    #get the quarterly store sales (by id and then by product class or brand)
    quarterly_trans = {}
    for j in range(4):
        #pull transaction data
        #across all stores in aggregate
        if stores == 'all':
            sql_where = Template('quarter = "Q$q"')
            trans_data = pullAll('transactions_rev','product_id,'+track,\
                                 sql_where.substitute(q = str(j+1)))
        #for one particular store
        elif type(stores) == int:
            sql_where = Template('(quarter,store_id) = ("Q$q",$s)')
            trans_data = pullAll('transactions_rev','product_id, '+track,\
                                 sql_where.substitute(q = str(j+1),s = str(stores)))
        #for each particular store
        else:
            sql_where = Template('quarter = "Q$q"')
            trans_data = pullAll('transactions_rev','product_id,'+track+',store_id',\
                                 sql_where.substitute(q = str(j+1)))
            
        #tally transaction data
        if stores == 'all' or type(stores) == int:
            quarterly_trans[j+1] = collections.Counter()
            if track == 'store_sales,store_cost':
                for id,sales,cost in trans_data:
                    #add quarterly sales data to the category relevant to product_id
                    quarterly_trans[j+1][product_class_lookups[id][1]] += sales - cost 
            if track == 'store_sales':
                for id,sales in trans_data:
                    #add quarterly sales data to the category relevant to product_id
                    quarterly_trans[j+1][product_class_lookups[id][1]] += sales 
        else:
            quarterly_trans[j+1] = {}
            if track == 'store_sales,store_cost':
                for id,sales,cost,store in trans_data:
                    if store not in quarterly_trans[j+1]:
                        quarterly_trans[j+1][store] = collections.Counter()
                    quarterly_trans[j+1][store][product_class_lookups[id]] += sales - cost
            if track == 'store_sales':
                for id,sales,store in trans_data:
                    if store not in quarterly_trans[j+1]:
                        quarterly_trans[j+1][store] = collections.Counter()
                    quarterly_trans[j+1][store][product_class_lookups[id]] += sales
            
    #print quarterly_trans
    return quarterly_trans

########################################
# Visualizing
########################################
def quarterlyRevByStore(viz=True,t='quarterly',track='sales'):
    '''
    Pulls quarterly or annual data (track) by store from revenueByQuarter()
    if viz==True: outputs plot of (t=)quarterly or annual (track=)sales or profit
    if viz==False, returns associated x:y dict from that data
    '''
    if track == 'sales': tr = 'store_sales'
    if track == 'profit': tr = 'store_sales,store_cost'
    #get the store_sales and possibly store_cost by category (for each individual store) 
    quarterly_store_rev = revenueByQuarter(mode = 'categories',stores = 'indiv',track=tr)
    #set of store_ids
    stores = set()
    for qtr in quarterly_store_rev.keys():
        for store in quarterly_store_rev[qtr].keys():
            stores.add(store)
    #to check for wacky data funny business
    print "There are this many stores:",len(stores)
    
    if viz:
        #plot total annual revenue by store_id
        fig = plt.figure()
        if t=='annual':
            #plot one point per store
            xlabs = sorted(stores) 
            ylabs = []
            for s_id in sorted(stores):         
                totSales = Decimal(0.0)
                for qtr,stores_dict in quarterly_store_rev.iteritems():
                    if s_id in stores_dict:
                        for cat,sales in stores_dict[s_id].iteritems():
                            totSales += sales
                ylabs.append(totSales)
            plt.suptitle('Annual '+track+' vs. store_id')
            plt.xlabel('store_id')
            plt.ylabel('Annual '+track+' (dollars)')
            plt.plot(xlabs,ylabs)
        if t=='quarterly':
            #plot one curve per store
            xlabs = range(1,5)
            for s_id in sorted(stores):
                y_store = []
                for qtr,stores_dict in quarterly_store_rev.iteritems():
                    totSales = Decimal(0.0)
                    for cat,sales in stores_dict[s_id].iteritems():
                        totSales += sales
                    y_store.append(totSales)
                plt.plot(xlabs,y_store)
            plt.legend(sorted(stores),bbox_to_anchor=(1, 0.8),\
                       bbox_transform=plt.gcf().transFigure)
            plt.suptitle('Quarterly '+track+' per store_id')
            plt.xticks(xlabs,['Q1','Q2','Q3','Q4'])
            plt.xlabel('Quarter (1997)')
            plt.ylabel(track+' (dollars)')
        plt.show()
    else:
        return dict.fromkeys(xlabs,ylabs)
    
def visBrandRevenue(quarter, topN):
    '''
    Brand revenue proportion plot (not very useful)
    quarter in (1,2,3,4,'average')
    topN should be an int and less than the total number of brands to track
    Calls quarterly revenue data from revenueByQuarter() (combining all outside topN to "other")
    '''
    #get the revenue dict
    if quarter == 'average':
        rev = collections.Counter()
        allQ = revenueByQuarter('brands')
        for qtr in allQ.keys():
            for key, val in allQ[qtr].iteritems():
                rev[key] += val
    elif quarter != 'average':
        rev = revenueByQuarter(mode)[quarter]
    total_rev = sum(rev.values())
    
    #labels and values to plot, by descending brand revenue share
    xlabs,yvals = [],[]
    for key,val in sorted(rev.iteritems(), key=operator.itemgetter(1),reverse=True):
        #since there are a lot of brands, break up into a tall "other" bar/plot
        if len(xlabs) < topN:
            xlabs.append(key)
            yvals.append(val/total_rev)
        if len(xlabs) == topN:
            xlabs.append('Other')
            yvals.append(Decimal(0.0))
        if len(xlabs) >= topN:
            yvals[-1] += val/total_rev
            
    #assemble the figure
    fig = plt.figure()
    #plot overlapping subfigs to get discontinuous y axis
    gs = gridspec.GridSpec(2, 1, height_ratios=[1,4])
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    #the indices where the bars go
    ind = np.arange(topN+1)
    width = 0.45
    #plot the same data on both axes
    ax.bar(ind, yvals, width, color='r')
    ax2.bar(ind, yvals, width, color='r')
    
    #limit view differently for parts of figure
    ax.set_ylim(float(yvals[-1]) - 0.125*1.2*float(yvals[0]), float(yvals[-1]) + 0.125*1.2*float(yvals[0]))  # outliers only
    ax2.set_ylim(0, 1.2*float(yvals[0]))  # most of the data
    ax.set_xlim(xmax = topN + 1)
    ax2.set_xlim(xmax = topN + 1)
    
    #hide the spines between ax and ax2
    ax.spines['bottom'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    # hide unwanted ticks and labels
    ax.xaxis.tick_top()
    ax.tick_params(labeltop='off')
    ax.set_yticks([0.540,0.545,0.550])
    
    #get discontinuous axis diagonal lines
    d = .015
    #top subplot
    kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
    ax.plot((1-d,1+d),(-4*d,+4*d), **kwargs) 
    ax.plot((-d,d),(-4*d,4*d), **kwargs) 
    #bottom subplot
    kwargs.update(transform=ax2.transAxes) 
    ax2.plot((1-d,1+d),(1-d,1+d), **kwargs) 
    ax2.plot((-d,d),(1-d,1+d), **kwargs)
    #titling and labeling
    plt.xlabel('Brand')
    plt.xticks(ind,xlabs,rotation=45)
    if quarter == 'average':
        fig.suptitle('Average Quarterly Revenue by Brand')
    else:
        fig.suptitle('Q'+str(quarter)+' Revenue by Brand')
    fig.text(0.02,0.65,'Proportion of store revenue',rotation=90)
    
    plt.show()
      
def profitWithinGroup(hier,nm):
    '''
    For some group nm at level of hierarchical product organization hier
    plots bar chart of rev/profit/cost for its children
    hier should be in tree (and not 'brand',which has no children)
    '''
    tree = ['product_family','product_department','product_category','product_class_id','brand']
    #get the names of the group's children
    hChild = getChildren(hier, nm)
    
    #plot total annual revenue by child
    fig = plt.figure()
    #lists for child names, profits, and costs
    xlabs,yvals,y2vals = [],[],[]
    width = 0.45
    for chld in hChild:
        #get [store_sales,store_cost] for chld, counting only transactions in nm and child
        revChild = revByTwoGroups((hier,nm.strip('"')),(tree[tree.index(hier)+1],chld))
        #skip children with no revenue (sounds like neo-liberalism)
        if revChild[0] == Decimal(0.0):
            continue
        xlabs.append(chld) #child name
        yvals.append(revChild[0]-revChild[1]) #child profit
        y2vals.append(revChild[1]) #child cost
    
    #convert any remaining product_class_ids to names
    xlabs = [x if isinstance(x,basestring) else productClassName(x) for x in xlabs]
    #sort everything by return on investment per child
    roi = [y/y2 for y,y2 in zip(yvals,y2vals)]
    yy2x = zip(roi,yvals,y2vals,xlabs)
    yy2x.sort(reverse=True)
    #plot the stacked bars, located by index ind
    ind = range(len(xlabs))    
    plt.bar(ind,[y for r,y,y2,x in yy2x],width,color='#5dade2',bottom=[y2 for r,y,y2,x in yy2x],label='Profit')
    plt.bar(ind,[y2 for r,y,y2,x in yy2x],width,color='#ec7063',label='Cost')
    #pyplot markup
    plt.suptitle('Annual revenue for '+hier+' '+nm)
    plt.xticks([x + width/2 for x in range(len(xlabs))],[x for r,y,y2,x in yy2x],rotation=45)
    plt.xlabel(tree[tree.index(hier)+1]+' (by decreasing ROI)')
    plt.ylabel('Annual dollars')
    plt.legend(loc='upper right')
    plt.show()
    
def profitByBrand(hier,nm):
    '''
    For a given group nm at hierarchical level hier
    plots bar chart of rev/profit/cost for the nm sales by brand 
    hier in ['product_family','product_department','product_category','product_class_id'] 
    '''
    #get hier and brand lookups
    #{product_id: [product_class_id,brand_name]}
    brandsByProduct_id = productClassLookups(mode='brand')
    #{product_class_id: [product_category,product_department,product_family]}
    product_cat_lookups = productCategoryLookups()
    
    #pull the transactions
    trans = pullAll('transactions_rev','product_id,store_sales,store_cost','store_cost > 0')
    
    #tally the revs and cost
    brandRevs = collections.Counter()
    brandCosts = collections.Counter()
    tree = ['product_class_id','product_category','product_department','product_family']
    lvl = tree.index(hier)
    for product_id,store_sales,store_cost in trans:
        #if hier requested is already product_class_id, tally right away
        if lvl == 0:
            if brandsByProduct_id[product_id][0] == nm:
                brandRevs[brandsByProduct_id[product_id][1]] += store_sales
                brandCosts[brandsByProduct_id[product_id][1]] += store_cost
        #if hier is higher(!), tally relevant membership group
        else:
            if product_cat_lookups[brandsByProduct_id[product_id][0]][lvl-1] == nm:
                brandRevs[brandsByProduct_id[product_id][1]] += store_sales
                brandCosts[brandsByProduct_id[product_id][1]] += store_cost 
                
    #plot total annual revenue by brand
    fig = plt.figure()
    #lists for brand names, profits, and costs
    xlabs,yvals,y2vals = [],[],[]
    width = 0.45
    for br in brandRevs.keys():
        xlabs.append(br) #brand name
        yvals.append(brandRevs[br] - brandCosts[br]) #brand profit
        y2vals.append(brandCosts[br]) #brand cost   
        
    #sort everything by return on investment per child
    roi = [y/y2 for y,y2 in zip(yvals,y2vals)]
    yy2x = zip(roi,yvals,y2vals,xlabs)
    yy2x.sort(reverse=True)
    #plot the stacked bars, located by index ind
    ind = range(len(xlabs))    
    plt.bar(ind,[y for r,y,y2,x in yy2x],width,color='#ec7063',bottom=[y2 for r,y,y2,x in yy2x],label='Profit')
    plt.bar(ind,[y2 for r,y,y2,x in yy2x],width,color='#5dade2',label='Cost')
    #pyplot markup
    if isinstance(nm,int):
        nm = productClassName(nm)
    plt.suptitle('Annual revenue for '+hier+' '+str(nm)+' by brand')
    plt.xticks([x + width/2 for x in range(len(xlabs))],[x for r,y,y2,x in yy2x],rotation=45)
    plt.xlabel('Brand (by decreasing ROI)')
    plt.ylabel('Annual dollars')
    plt.legend(loc='upper right')
    plt.show()

#quarterlyRevByStore(t='quarterly',track='profit')   
#profitWithinGroup('product_department', '"Health and Hygiene"') 
#profitByBrand('product_family', 'Drink')    
#visBrandRevenue('average', 20)