import argparse
import data_utils as du
from tbl_kg_mapper import Tbl2KgMapper

'''
    Set up the arguments and parse them.
'''


def get_arguments():
    parser = argparse.ArgumentParser(description='Use this script to construct the WikiTablesKG from the TableNet tables.')
    parser.add_argument('-i', '--tables', help='The table input file.', required=True)
    parser.add_argument('-dl', '--data_limit', help='The maximum number of tables we export to the KG.', required=True, type=int)
    parser.add_argument('-o', '--out_dir', help='The output directory for storing the embeddings.', required=True)
    parser.add_argument('-t', '--taxonomy', help='The path to the flat category taxonomy.', required=True)
    parser.add_argument('-ec', '--entity_cat', help='The path to the entity category associations.', required=True)
    parser.add_argument('-gt', '--ground_truth', help='The ground-truth table pairs.', required=False)
    parser.add_argument('-s', '--start_offset', help='The start offset for loading the tables', type=int, default=0)
    parser.add_argument('-sf', '--file_suffix', help='The file suffix')
    return parser.parse_args()


def load_data(tables_file, taxonomy_path, ecats_path, limit, start=0):
    # load the flat taxonomy
    tax = du.load_flat_cat_tax(taxonomy_path)
    print('Loaded the taxonomy data with {:d} instances.'.format(len(tax)))

    # load the entity category associations
    ecats = du.load_entity_cats(ecats_path)
    print('Loaded the entity category data with {:d} instances.'.format(len(ecats)))

    tables = du.load_tables(tables_file, start=start, limit=limit, random_sample=True, tax=tax, ecats=ecats)
    print('Loaded {:d} tables.'.format(len(tables)))

    return tables


if __name__ == '__main__':
    arg = get_arguments()

    tables = load_data(tables_file=arg.tables, taxonomy_path=arg.taxonomy, ecats_path=arg.entity_cat, start=arg.start_offset, limit=arg.data_limit)
    tbl_mapper = Tbl2KgMapper(tables=tables, out_dir=arg.out_dir, suffix=arg.file_suffix)
    tbl_mapper.write_tables()
