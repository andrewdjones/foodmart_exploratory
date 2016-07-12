# foodmart_exploratory
Code base for business analysis of "foodmart"

#Rough plan
1. Build some my_sql tables in case others need to use the data for lookups and for speedy exploratory queries (foodmart_mysql_explo.py)
[N.B.: my tables differ from the foodmart database, even after cleaning, so I'll stick with the corrected version of what I have.]

2. Get some rudimentary stats about the data (product_cats_brands.py)

3. Build a matplotlib simple histogram for brand sales data (product_cats_brands.py); consider some tables which list brand sales (and profits) by category or department (since the full set would be too large for easy readability.
[the category sales data overlayed histogram builds an approximation, but it's not promising; the overall brand sales histogram gives an idea of the revenue proportions captured by the topN brands, which is not especially informative]

3. Use networkx to produce some graph visualizations for category data (category_graph.py)
[currently builds the literally correct graph, but it's not visually helpful; also needs optimized layout, if time permits?]

4. Expand product offerings and get stats on profitability and sales (products_and_profits.py)

#Interlude: data cleaning problem
There appears to be exactly twice as much transaction data as foodmart intends to record.

-There are 86802 rows of transactions corresponding to 13 store_ids (all <= 24), all of which have promotional_ids > 24 (when 1997 starts) or 0 (no promo) 

-There are 86802 rows below those corresponding to a huge number of "store_ids" above 24.  Each of those rows has a promotional_id <= 24, corresponding to a date in 1996, while the transaction data only lists/covers 1997.

Upon closer examination, all of this second set of rows appears to duplicate the first set up to a reordering of the columns:

-1st set cols: [product_id,customer_id,store_id,promotional_id,...]

-2nd set cols: [product_id,promotional_id,customer_id,store_id,....]

To confirm, I went back to the online source, where the author provides downloads and instructions for building the entire foodmart mysql database, which I cloned on my local machine.  The transaction data pre-loaded into his tables matches the "1st set" of my data almost exactly, while the 2nd set is nowhere to be seen.  It also looks like four transactions have been removed from the (corrected) data at random.  These are either csv export errors from the original mysql table or a quick quiz to make sure I sanity-check my data.

With that in mind, I'm going to cut all that duplicate data (the "2nd set" of 86802 transactions) from my stats and viz

#Sales factors
Ideas to consider:
Total revenue and profit looks relatively stable across quarters.  What about across stores?
Stores 2, 7, and 14 have the lowest total revenues and profits, by far.
