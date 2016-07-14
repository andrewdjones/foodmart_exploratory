########################################
#Code base for Foodmart recommendations
#csv datasets from https://sites.google.com/a/
#dlpage.phi-integration.com/pentaho/mondrian/mysql-foodmart-database/foodmart_mysql.tar.gz
#
#This python file sets up my_sql databases
#to make sure I remember how
#
#Andrew Jones
#andrew.d.jones@yale.edu
#July 2016
########################################

import mysql.connector
from mysql.connector.connection import MySQLConnection
from _sqlite3 import DatabaseError, ProgrammingError
import csv
from string import Template
import collections

def makeTable(tName,cols):
    '''
    Makes simple sql table named tName
    cols input format (col1 varchar(100),col2 int(5),...)
    '''
    #set up sql connection
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    #make the table
    querytype = Template("CREATE TABLE "+tName+"($c)")
    query = querytype.substitute(c = ','.join(cols))
    cursor.execute(query)
    conn.commit()
    #close the connection
    cursor.close()
    conn.close()

def tableFromCSV(csvName,cats,catTypes,tableName):
    '''
    Takes a csv (csvName) full of data columns
    Extracts columns corresponding to list cats (of data type list catTypes)
    Sticks result in an sql table named tableName
    '''
      
    #make the table, unless it already exists
    try:
        makeTable(tableName, [cats[j]+' '+catTypes[j] for j in range(len(catTypes))])        
    except mysql.connector.errors.ProgrammingError:
        raise NameError('Careful! That table already exists.')
    
    #open the csv
    fp = csv.reader(open(csvName,'r'))
    #pull the relevant categories
    csvCols = fp.next()
    csvCols = [c.strip() for c in csvCols]
    #these indices will locate columns in the csv
    catIndices = [csvCols.index(catName) for catName in cats]
    #these strings will cue the sql database
    sqlVals = ["%s" for j in cats]
    
    #insert the data 
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    for row in fp:
        querytype = Template("INSERT INTO "+tableName+" ($c) VALUES($v)")#(col1,col2),(%s,%s)
        query = querytype.substitute(c = ",".join(cats), v = ",".join(sqlVals))
        args = [row[i].strip(" '") for i in catIndices]
        cursor.execute(query,tuple(args))
        conn.commit()

def pullAll(tableName,getCol,constraint,op='none'):
    '''
    Looks at table tableName and selects/prints all the data subject to constraint
    Outputs printing (op = 'print') or csv writing (op = 'csv')
    and returns the list of constrained outputs
    '''
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    querytype = Template("SELECT $g FROM $t WHERE $c")
    query = querytype.substitute(g = getCol,t = tableName,c = constraint)
    cursor.execute(query)
    rows = cursor.fetchall()
    if op == 'print':
        for row in rows:
            print row
    elif op == 'csv':
        fp = Template('$t pull $c output.csv')
        csvName = fp.substitute(t=tableName,c=constraint)
        x = csv.writer(open(csvName, 'wb'))
        for row  in rows:
            x.writerow(row)
    else:
        pass
    return rows

'''
tableFromCSV('raw_data/promotion_clean.csv',\
             ['promotion_id','promotion_district_id','promotion_name',\
              'media_type','cost'],\
             ['int(4)','int(3)','varchar(50)',\
              'varchar(50)','int(5)'],'promotion')
tableFromCSV('raw_data/product.csv',\
             ['product_class_id','product_id','brand_name',\
              'product_name'],\
             ['int(3)','int(4)','varchar(50)',\
              'varchar(50)'],'product')
tableFromCSV('raw_data/product_class.csv',\
             ['product_class_id','product_subcategory','product_category',\
              'product_department', 'product_family'],\
             ['int(3)','varchar(50)','varchar(50)',\
              'varchar(50)','varchar(50)'],'product_class')
tableFromCSV('raw_data/transactions_clean.csv',\
             ['product_id','customer_id','store_id','promotion_id',\
              'month_of_year', 'quarter','the_year','store_sales',\
              'store_cost','unit_sales'],\
             ['int(4)','int(5)','int(5)','int(4)',\
              'int(2)','varchar(50)','int(4)','decimal(10,4)',\
              'decimal(10,4)','int(5)'],'transactions_rev')
'''