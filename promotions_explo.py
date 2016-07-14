########################################
#Code base for Foodmart recommendations
#csv datasets from https://sites.google.com/a/
#dlpage.phi-integration.com/pentaho/mondrian/mysql-foodmart-database/foodmart_mysql.tar.gz
#
#This python file contains exploratory code for promotions
#
#Andrew Jones
#andrew.d.jones@yale.edu
#July 2016
########################################
import mysql.connector
from mysql.connector.connection import MySQLConnection
from _sqlite3 import DatabaseError, ProgrammingError
from foodmart_mysql_explo import pullAll
from collections import Counter
from decimal import Decimal
import operator
import timeit
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as colors
import numpy as np

########################################
# Labeling
########################################
def getPromoLookups(quer):
    '''
    returns dict { promotional_id1: quer1, promotional_id2: quer2,...}
    quer should be whatever promo_id will map to
    ['promotion_district_id','promotion_name','media_type','cost']
    '''
    promo_id_lookups = {}
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    query = "SELECT promotion_id, "+quer+" FROM promotion"
    cursor.execute(query)
    allPromos = cursor.fetchall()
    for p, l in allPromos:
        promo_id_lookups[p] = l
    return promo_id_lookups

########################################
# Calculating
########################################
def promoByTransaction(track):
    '''
    Returns dict {promotion_id: tracked statistic}
    based on all annual transaction data involving promotions
    '''
    #tallies
    promoRev = Counter()
    promoCost = Counter()
    promoUnits = Counter()
    promoTransactions = Counter()
    
    #pull the transactions, add stats to tallies
    #this is slow, but I didn't need to run it often
    for p in range(1897):
        if p == 0:  continue
        all_p = pullAll('transactions_rev','store_sales,store_cost,unit_sales',\
                        'promotion_id = '+str(p))
        if len(all_p) == 0:
            continue
        for t in all_p:
            promoRev[p] += t[0]
            promoCost[p] += t[1]
            promoUnits[p] += t[2]
            promoTransactions[p] += 1.0
    
    #from tallied stats, output requested dict type
    if track == 'transactions':
        st = promoTransactions
    if track == 'transactions per dollar':
        pcost = getPromoLookups('cost')
        st = {k: promoTransactions[k]/pcost[k] for k in promoRev.keys()}
    if track == 'roi':
        st = {k: (promoRev[k] - promoCost[k])/promoCost[k] for k in promoRev.keys()}
    if track == 'sales':
        st = promoRev
    if track == 'cost':
        st = promoCost
    if track == 'profit':
        st = {k: promoRev[k] - promoCost[k] for k in promoRev.keys()}
    if track == 'sales per unit':
        st = {k: promoRev[k]/promoUnits[k] for k in promoRev.keys()}
    if track == 'profit per unit':
        st = {k: (promoRev[k] - promoCost[k])/promoUnits[k] for k in promoRev.keys()}
    if track == 'profit per dollar':
        pcost = getPromoLookups('cost')
        st = {k: (promoRev[k] - promoCost[k])/pcost[k] for k in promoRev.keys()}
    if track == 'profit per transaction':
        st = {k: (promoRev[k] - promoCost[k])/promoTransactions[k] for k in promoRev.keys()}
    #print sorted(st.iteritems(),key=operator.itemgetter(1),reverse=True)
    return st

########################################
# Visualizing
########################################
def get_cmap(n):
    '''
    Returns function that maps each index in 0, 1, ... n-1 to a distinct RGB color.
    For large n, they won't be easily distinguishable
    '''
    color_norm  = colors.Normalize(vmin=0, vmax=n-1)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='hsv') 
    def map_index_to_rgb_color(index):
        return scalar_map.to_rgba(index)
    return map_index_to_rgb_color

def promoViz(t1,t2,by='id'):
    '''
    Plots promotional stats by metrics t1 and t2 (from promoByTransaction(t))
    if by=='id', displays results indexed by promotional_id
    if by=='media', displays results indexed by promo media_type
        NB: media types are odd, as some promos have in multiple media types
    (ti should be in ['roi','sales','cost','profit','sales per unit','profit per unit'])
    '''
    p1_by_id = promoByTransaction(t1)
    p2_by_id = promoByTransaction(t2)
    #if tallying by promo_id, don't need other lookups
    if by=='id':
        p1,p2 = p1_by_id,p2_by_id
    #if tallying by media type, need additional hash
    elif by=='media':
        #promo to media lookups
        promoID_to_media = getPromoLookups('media_type')
        #no promo needs a media type, too
        promoID_to_media[0] = 'none'
        
        #group the data by media_type
        media_type_size,p1,p2 = Counter(),Counter(),Counter()
        for k,v in p1_by_id.iteritems():
            p1[promoID_to_media[k]] += v
            media_type_size[promoID_to_media[k]] += 1
        for k,v in p2_by_id.iteritems():
            p2[promoID_to_media[k]] += v
            media_type_size[promoID_to_media[k]] += 1
    
    #plot
    fig = plt.figure()
    colors = get_cmap(len(p1.keys()))
    for i,p_id in enumerate(p1.keys()):
        plt.scatter(p1[p_id],p2[p_id],s=30*media_type_size[p_id],label=p_id,c=colors(i))
    #pyplot markup
    plt.suptitle('Performance of each promotional media type')
    plt.title
    plt.xlabel(t1+' promotional cost')
    plt.ylabel(t2+' promotional cost')
    plt.legend(loc='lower right',scatterpoints=1)
    plt.show()

promoViz('profit per dollar','transactions per dollar',by='media')