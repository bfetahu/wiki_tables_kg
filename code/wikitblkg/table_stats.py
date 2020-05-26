import argparse
import gzip
import json

import data_utils as du
from data_prep.table import Table


def get_arguments():
    parser = argparse.ArgumentParser(description='Use this script to construct the WikiTablesKG from the TableNet tables.')
    parser.add_argument('-i', '--tables', help='The table input file.', required=True)
    parser.add_argument('-o', '--out_dir', help='The output directory for storing the embeddings.', required=True)
    parser.add_argument('-t', '--taxonomy', help='The path to the flat category taxonomy.', required=True)
    parser.add_argument('-ec', '--entity_cat', help='The path to the entity category associations.', required=True)
    return parser.parse_args()


def gather_table_stats(infile, out_file, tax=None, ecats=None):
    if infile.endswith('gz'):
        reader = gzip.open(infile, 'r')
    else:
        reader = open(infile, 'r')

    # read the tables data
    fout = open(out_file, 'a', encoding='utf_8')
    out_str = ''
    for line in reader:
        # parse the entity table json
        entity_json = json.loads(line.strip())
        entity_label = entity_json['entity']

        # iterate through the sections
        for section in entity_json['sections']:
            section_label = section['section']

            for table in section['tables']:
                tbl_obj = Table(flat_taxonomy=tax, ecats=ecats)
                tbl_obj.load_json(table, entity_label, section_label)

                table_out = '{:d}\t{}\t{}\t{:d}'.format(tbl_obj.table_id, tbl_obj.entity, tbl_obj.section, len(tbl_obj.table_rows))

                for col_idx, column in enumerate(tbl_obj.columns):
                    tbl_col_out = '{}\t{:d}\t{}\t{}\n'.format(table_out, col_idx, column, tbl_obj.column_types[column])
                    out_str += tbl_col_out

            if len(out_str) > 100000:
                fout.write(out_str)
                out_str = ''
    fout.write(out_str)
    fout.close()


if __name__ == '__main__':
    arg = get_arguments()

    # load the flat taxonomy
    tax = du.load_flat_cat_tax(arg.taxonomy)
    print('Loaded the taxonomy data with {:d} instances.'.format(len(tax)))

    # load the entity category associations
    ecats = du.load_entity_cats(arg.entity_cat)
    print('Loaded the entity category data with {:d} instances.'.format(len(ecats)))

    out_file = arg.out_dir + '/table_stats.tsv'
    gather_table_stats(arg.tables, out_file, tax, ecats)
