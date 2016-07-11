########################################
#Code base for Foodmart recommendations
#csv datasets from https://sites.google.com/a/
#dlpage.phi-integration.com/pentaho/mondrian/mysql-foodmart-database/foodmart_mysql.tar.gz
#
#This python file constructs statistical visualizations for product data
#both for categories of product and brands
#based on networkx graphs
#
#Andrew Jones
#andrew.d.jones@yale.edu
#July 2016
########################################

import networkx as nx
from product_cats_brands import *
import matplotlib.pyplot as plt
from xml.dom.minicompat import NodeList

def simpleShell():
    '''
    Spits out a messy but accurate graph of category membership
    '''
    #build counter of average revenue per quarter, hashed by product_category
    allQ = revenueByQuarter()
    rev = collections.Counter()
    for qtr in allQ.keys():
        for key, val in allQ[qtr].iteritems():
            rev[key] += val
    total_rev = sum(rev.values())
    
    #get the product_category membership data (department and family)
    product_paths = productCategoryLookups()
    
    #construct the graph
    G=nx.Graph()
    fam_set = set()
    dep_set = set()
    cat_set = set()
    #add nodes and edges
    for prod,memb in product_paths.iteritems():
        #add nodes
        G.add_nodes_from(memb)
        fam_set.add(memb[2])
        dep_set.add(memb[1])
        cat_set.add(memb[0])
        #add edges
        #category - department
        G.add_edge(memb[0],memb[1])
        #department - family
        G.add_edge(memb[1],memb[2])
    #shell sorting and coloring
    shells = [[],[],[]]
    cols = []
    for j in fam_set:
        shells[0].append(j)
        cols.append('b')
    for j in dep_set:
        shells[1].append(j)
        cols.append('y')
    for j in cat_set:
        shells[2].append(j)
        cols.append('r')
    
    #shell positions
    p0 = nx.shell_layout(G,nlist=shells)
    #p1 = nx.fruchterman_reingold_layout(G,pos = p0)
    #draw and show
    nx.draw(G,pos=p0,nodelist = shells[0]+shells[1]+shells[2], node_color = cols)
    plt.show()
    
simpleShell()
    



