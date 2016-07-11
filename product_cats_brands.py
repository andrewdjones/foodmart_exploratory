########################################
#Code base for Foodmart recommendations
#csv datasets from https://sites.google.com/a/
#dlpage.phi-integration.com/pentaho/mondrian/mysql-foodmart-database/foodmart_mysql.tar.gz
#
#This python file constructs statists for product data
#both for categories of product and brands
#plus simple visualizations for brands
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
from string import strip

'''
Plan:
1. From transaction data, pull all unit store_sales, store_cost, unit_sales, and quarter/year dates by product_id
2. From product data, connect all product_id values to product_class_id and brand_name
3. From product_class_id data, get product_category, product_department, product_family
Visuals:
Hierarchical bar for percentage of (quarterly?) sales revenue by category, dept, and family
'''

def productClassLookups(mode = 'class_id'):
    '''
    If mode == class_id: Returns dict where (key,val) = (product_id, associated product_class_id)
    If mode == brand: (key,val) = (product_id, associated brand_name)
    '''
    product_id_lookups = {}
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    if mode == 'class_id':
        query = "SELECT product_class_id, product_id FROM product"
    elif mode == 'brand':
        query = "SELECT brand_name, product_id FROM product"
    cursor.execute(query)
    allProds = cursor.fetchall()
    for p_class, p_id in allProds:
        product_id_lookups[p_id] = p_class
    return product_id_lookups

def productCategoryLookups():
    '''
    Returns dict where (key,val) = (product_class_id, [product_category, product_dept, product_fam])
    '''
    product_class_lookups = {}
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT product_class_id, product_category, product_department, product_family FROM product_class"
    cursor.execute(query)
    allProds = cursor.fetchall()
    for p_data in allProds:
        product_class_lookups[p_data[0]] = p_data[1:]
    return product_class_lookups

def categoryDepartmentLookups():
    '''
    Returns dict where (key,val) = (product_category, [product_department, product_family])
    WARNING: doing some funny business and assigning membership based on the last particular
    dept/family a given product_class_id happens to cue in-category
    '''
    cat_dept_lookups = {}
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT product_category, product_department, product_family FROM product_class"
    cursor.execute(query)
    allProds = cursor.fetchall()
    for p_data in allProds:
        cat_dept_lookups[p_data[0]] = p_data[1:]
    return cat_dept_lookups

def getDepByFam(f):
    '''
    For a given product_family f, returns a set of all the departments in it
    '''
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT product_department FROM product_class WHERE product_family = "+f
    cursor.execute(query)
    fam_dep = set()
    for p in cursor.fetchall():
        fam_dep.add(strip(p[0],'u()"'))
    return fam_dep

def revenueByQuarter(mode = 'categories'):
    '''
    Returns a dict hashed by quarter (1-4), where each entry is a counter:
    if mode == brands, counter tallies quarterly store sales by brand
    if mode == categories, counter tallies quarterly store sales by product_category
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
        product_class_lookups= productClassLookups(mode = 'brand')
    
    #get the quarterly store sales (by id and then by product class or brand)
    quarterly_trans = {}
    for j in range(4):
        quarterly_trans[j+1] = collections.Counter()
        trans_data = pullAll('transactions','product_id, store_sales','quarter = "Q'+str(j+1)+'"')
        for id,sales in trans_data:
            #add quarterly sales data to the category relevant to product_id
            quarterly_trans[j+1][product_class_lookups[id]] += sales 
            
    #print quarterly_trans
    return quarterly_trans
    
def visualizeRevenue(quarter, topN, mode='categories'):
    '''
    Calls quarterly revenue data from revenueByQuarter() (combining all outside topN to "other")
    if mode==brands: plots bar chart of revenue share by brand (implemented fine)
    if mode==categories: plots hierarchical bar chart of revenue share by category, dept, family 
    WARNING: categories mode is under construction and isn't well-defined, given that some categories
    belong in more than one department
    '''
    #get the revenue dict
    rev = collections.Counter()
    if quarter == 'average':
        allQ = revenueByQuarter(mode = mode)
        for qtr in allQ.keys():
            for key, val in allQ[qtr].iteritems():
                rev[key] += val
    total_rev = sum(rev.values())
    
    if mode == 'brands':
        #labels and values to plot
        xlabs,yvals = [],[]
        for key,val in sorted(rev.iteritems(), key=operator.itemgetter(1),reverse=True):
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
        ind = np.arange(topN+1)    # the x locations for the groups
        width = 0.45       # the width of the bars: can also be len(x) sequence
        # plot the same data on both axes
        ax.bar(ind, yvals, width, color='r')
        ax2.bar(ind, yvals, width, color='r')
        
        # limit view differently for parts of figure
        ax.set_ylim(float(yvals[-1]) - 0.125*1.2*float(yvals[0]), float(yvals[-1]) + 0.125*1.2*float(yvals[0]))  # outliers only
        ax2.set_ylim(0, 1.2*float(yvals[0]))  # most of the data
        ax.set_xlim(xmax = topN + 1)
        ax2.set_xlim(xmax = topN + 1)
        
        # hide the spines between ax and ax2
        ax.spines['bottom'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        # hide unwanted ticks and labels
        ax.xaxis.tick_top()
        ax.tick_params(labeltop='off')
        ax2.xaxis.tick_bottom()
        ax.set_xticklabels(ax.xaxis.get_majorticklabels(), rotation=45)
        #ax.set_yticks([0.540,0.545,0.550])
        # get discontinuous axis diagonal  lines
        d = .015
        # arguments to pass to plot diag lines
        # top subplot
        kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
        ax.plot((1-d,1+d),(-4*d,+4*d), **kwargs) 
        ax.plot((-d,d),(-4*d,4*d), **kwargs) 
        # bottom subplot
        kwargs.update(transform=ax2.transAxes) 
        ax2.plot((1-d,1+d),(1-d,1+d), **kwargs) 
        ax2.plot((-d,d),(1-d,1+d), **kwargs)
        if quarter == 'average':
            fig.suptitle('Average Quarterly Revenue by Brand')
        else:
            fig.suptitle('Q'+str(quarter)+' Revenue by Brand')
            
    #NB: doesn't really work, since some categories have more than one parent        
    if mode == 'categories':
        #get the department and family memberships
        cat_dep_lookups = categoryDepartmentLookups()
        family_rev = collections.Counter()
        department_rev = collections.Counter()
        family_contents = {}
        department_contents = {}
        for cat,sls in rev.iteritems():
            department_rev[cat_dep_lookups[cat][0]] += sls
            family_rev[cat_dep_lookups[cat][1]] += sls
            try:
                family_contents[cat_dep_lookups[cat][1]].append(cat)
            except KeyError:
                family_contents[cat_dep_lookups[cat][1]] = [cat]
            try:
                department_contents[cat_dep_lookups[cat][0]].append(cat)
            except KeyError:
                department_contents[cat_dep_lookups[cat][0]] = [cat]
        #print family_contents
        
        #assemble the figure
        fig = plt.figure()
        #plot the families    
        x3labs,y3vals = [],[]
        width = 0.45       # the width of the bars: can also be len(x) sequence
        widths = []
        for key,val in sorted(family_rev.iteritems(), key=operator.itemgetter(1),reverse=True):    
            x3labs.append(key)
            y3vals.append(val/total_rev)  
            widths.append(width*len(family_contents[key]))
        ind = [0]
        for j in range(len(widths)-1):
            ind.append(ind[-1]+widths[j])
        ax3 = plt.subplot()
        ax3.bar(ind,y3vals,widths,color='b')
        
        #plot the departments, ordered by descending revenue in each product_family
        x2labs,y2vals = [],[]
        widths = []
        for fam in x3labs:
            fam_deps = getDepByFam('"'+fam+'"')
            for dep,r in sorted(department_rev.iteritems(),key=operator.itemgetter(1),reverse=True):
                if dep in fam_deps:
                    x2labs.append(dep)
                    y2vals.append(r/total_rev)
                    widths.append(width*len(department_contents[dep]))
        ind = [0]
        for j in range(len(widths)-1):
            ind.append(ind[-1]+widths[j])
        ax2 = plt.subplot()
        ax2.bar(ind,y2vals,widths,color='y')
        
        #now the category data
        ax = plt.subplot()  
        xlabs,yvals = [],[]
        for key,val in sorted(rev.iteritems(), key=operator.itemgetter(1),reverse=True):
            xlabs.append(key)
            yvals.append(val/total_rev)
        ax.bar([width*x for x in range(len(xlabs))], yvals, width, color='r')
        #ax2.set_xlim(xmax = topN + 1)
        #overlay the summed 
        if quarter == 'average':
            fig.suptitle('Average Quarterly Revenue by Category')
        else:
            fig.suptitle('Q'+str(quarter)+' Revenue by Category')
        
    fig.text(0.02,0.65,'Proportion of store revenue',rotation=90)
    #ax.title('Brand')
    #plt.xticks(ind + width/2., x2labs, rotation=45)
    
    plt.show()


visualizeRevenue('average', 45, mode = 'categories')
#revenueByQuarter(mode='categories')