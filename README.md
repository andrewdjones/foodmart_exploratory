# foodmart_exploratory
Code base for business analysis of "foodmart".

More thorough explanation exists in the accompanying report, and commenting is done in-code.

#Rough layout
1. Build some my_sql tables in case others need to use the data for lookups and for speedy exploratory queries (foodmart_mysql_explo.py)
[N.B.: my tables differ from the online foodmart database, even after cleaning, so I'll stick with the corrected version of what I have.]

2. Visualize the inventory grouping hierarchy (category_graph.py; networkx and graphviz).

3. Get stats and visualizations on the products and brands (product_cats_brands.py; mysql and matplotlib)

4. Get stats on profitability and cost of promotions (promotions_explo.py)
