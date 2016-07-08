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

#generic sql table maker
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

#builds table from csv    
def tableFromCSV(csvName,cats,catTypes,tableName):
    '''
    Takes a csv full of data columns
    Extracts columns corresponding to cats (of data type catTypes)
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

#sends queries, outputs results
def pullAll(tableName,constraint,op='print'):
    '''
    Looks at table tableName and selects/prints all the data subject to constraint (ex.: col1 > 2)
    '''
    conn = mysql.connector.connect(host='localhost',database='my_sql',user='root',password='recordsaredope')
    cursor = conn.cursor()
    querytype = Template("SELECT * FROM $t WHERE $c")
    query = querytype.substitute(t = tableName,c = constraint)
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
        raise NameError('What kind of output? (print, csv)')

#pullAll('product_class','product_department = "Dairy"')
'''
tableFromCSV('raw_data/product_class.csv',\
             ['product_class_id','product_subcategory','product_category',\
              'product_department', 'product_family'],\
             ['int(3)','varchar(50)','varchar(50)',\
              'varchar(50)','varchar(50)'],'product_class')
'''
'''
tableFromCSV('raw_data/transactions.csv',\
             ['product_id','customer_id','store_id','promotion_id',\
              'month_of_year', 'quarter','the_year','store_sales',\
              'store_cost','unit_sales'],\
             ['int(4)','int(5)','int(5)','int(4)',\
              'int(2)','varchar(50)','int(4)','decimal(10,4)',\
              'decimal(10,4)','int(5)'],'transactions')
'''