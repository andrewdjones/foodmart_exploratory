########################################
#Code base for Foodmart recommendations
#csv datasets from https://sites.google.com/a/
#dlpage.phi-integration.com/pentaho/mondrian/mysql-foodmart-database/foodmart_mysql.tar.gz
#
#This python file constructs networkx/graphviz visualizations for hierarchical data
#Automated graph drawing is hard, so be gentle
#Captures the complexity of the hierarchy (multiple parenthood)
#
#Andrew Jones
#andrew.d.jones@yale.edu
#July 2016
########################################
import graphviz as gv
import networkx as nx
from product_cats_brands import *
import matplotlib.pyplot as plt


def simpleShell():
    '''
    Spits out a messy but accurate graph of category membership
    Nodes are categories, departments, and families
    Edges are 'is a parent/child of' relations (NOT one-to-one)
    '''
    #build counter of average revenue per quarter, hashed by product_category
    catRev = revByGroup('product_category')
    #rev by department
    depRev = revByGroup('product_department')
    #rev by family
    famRev = revByGroup('product_family')
    
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
    sizes = []
    for j in famRev:
        shells[0].append(j)
        cols.append('#5dade2')#blueish
        sizes.append(famRev[j][0])
    for j in depRev:
        shells[1].append(j)
        cols.append('#f7dc6f')#yellowish
        sizes.append(depRev[j][0])
    for j in catRev:
        shells[2].append(j)
        cols.append('#ec7063')#reddish
        sizes.append(catRev[j][0])
    #normalization so sizes display reasonably (but proportionally)
    sizes = [round(x/100) for x in sizes]
    #print(sizes)
    
    #shell positions
    #alternate node position options to play around with
    #p0 = nx.shell_layout(G,nlist=shells)
    #p0 = nx.fruchterman_reingold_layout(G,pos = p0)
    #reasonably intuitive node positions
    p0 = nx.nx_pydot.graphviz_layout(G,prog='sfdp')
    #draw and show
    nx.draw(G,pos=p0,width=1, nodelist = shells[0]+shells[1]+shells[2],\
            node_size = sizes, node_color = cols, scale = 6,\
            font_size = 12, with_labels = False)
    #put the labels a little above the nodes themselves
    nx.draw_networkx_labels(G,pos={k:(v[0],v[1]+10) for k,v in p0.iteritems()})
    
    plt.show()
    
simpleShell()