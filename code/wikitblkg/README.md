# WikiTablesKG 

In this repository, we have published code that extracts statistics from the TableNet dataset, and furthermore generates the knowledge graph according to the WikiTablesKG paper.


## Extract WikiTablesKG

To extract the WikiTablesKG from the tables coming from the TableNet dataset, please run the following command:

`python extract_graph.py -i tbl_file_path -o . -t category_taxonomy_path -ec entity_category_assoc_file -sf output_file_suffix -dl num_tables_to_parse -s num_tables_to_skip`

## Extract Statistics

### Table Stats

In order to extract the table stats from TableNet. Please run the following command:

`python table_stats.py -i tbl_file_path -o . -t category_taxonomy_path -ec entity_category_assoc_file`


The stats output are of the following type:

`[TABLE ID] [TABLE Entity] [Entity Section] [Num Table Rows] [Column Index] [Column Name] [Column Type]`


### WikiTablesKG Stats
In order to extract the stats from the WikiTablesKG knowledge graph. Please run the following command:

`python kg_stats.py -i kg_input_files -o . -f a`

The output from this process are several files containing various KG statistics.
*  Number of columns per table
*  Number of cells per table
*  Column type statistics
*  Cell type statistics 
*  Column and cell value association statistics
