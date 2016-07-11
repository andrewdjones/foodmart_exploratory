# foodmart_exploratory
Code base for business analysis of "foodmart"

#Rough plan
1. Build some my_sql tables in case others need to use the data for lookups and for speedy exploratory queries (foodmart_mysql_explo.py)
2. Get some rudimentary stats about the data (product_cats_brands.py)
3. Build a matplotlib simple histogram for brand sales data (product_cats_brands.py)
[the category sales data overlayed histogram builds an approximation, but it's not promising]
3. Use networkx to produce some graph visualizations for category data (category_graph.py)
[currently builds the literally correct graph, but it's not visually helpful]
[also needs sizing/weighting and optimized edge crossings]