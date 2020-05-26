import argparse
import gzip
import os
from collections import defaultdict
from os.path import isfile, join


def get_arguments():
    parser = argparse.ArgumentParser(description='Use this script to construct the WikiTablesKG from the TableNet tables.')
    parser.add_argument('-i', '--input_kg_files', help='The input knowledge graph files.', required=True)
    parser.add_argument('-o', '--out_dir', help='The output directory for storing the stats embeddings.', required=True)
    parser.add_argument('-f', '--stats_flag', help='Determine the type of statistics we want to extract', required=True, default='a')
    return parser.parse_args()

'''
    Extract the number of triples per table.
'''
def __num_triples_per_table(in_file, out_dir, skip_lines=7):
    fin = gzip.open(in_file, 'rt', encoding='utf_8')

    table_data = {}
    buffer_ = []
    table_id = None
    for line_idx, line in enumerate(fin):
        if line_idx < skip_lines:
            continue

        if 'a tn:Table' in line:
            tmp_tbl_id = line.strip().split(' ')[0]
            if table_id is not None:
                table_data[table_id] = len(buffer_)
                buffer_.clear()

                # change the table ID
                table_id = tmp_tbl_id
            else:
                table_id = tmp_tbl_id
        else:
            buffer_.append(line.strip().split(' '))

    table_data[table_id] = len(buffer_)

    #write the output
    out_str = ''
    fout = open(out_dir + '/num_triples_per_table.tsv', 'a', encoding='utf_8')
    for tbl_id in table_data:
        out_str += '{}\t{:d}\n'.format(tbl_id, table_data[tbl_id])

        if len(out_str) > 10000:
            fout.write(out_str)
            out_str = ''
    fout.write(out_str)
    fout.close()


def __parse_kg_by_table(in_file, out_dir, skip_lines=7):
    fin = gzip.open(in_file, 'rt', encoding='utf_8')

    table_data = defaultdict(list)
    buffer_ = []
    table_id = None
    count = 0
    for line_idx, line in enumerate(fin):
        if line_idx < skip_lines:
            continue

        if 'a tn:Table' in line:
            tmp_tbl_id = line.strip().split(' ')[0]
            if table_id is not None:
                table_data[table_id].extend(buffer_)
                buffer_.clear()

                # change the table ID
                table_id = tmp_tbl_id

                # process the table data every 100 tables.
                if len(table_data) % 10000 == 0:
                    num_cols, num_rows, num_cells, col_types, cell_types, cell_column = __parse_table_stats(table_data)
                    __write_stats(out_dir, num_cols, num_rows, num_cells, col_types, cell_types, cell_column)

                    count += 10000
                    print('Processed {:d} table stats so far...'.format(count))

                    table_data.clear()
            else:
                table_id = tmp_tbl_id
        else:
            buffer_.append(line.strip().split(' '))

    # process the table data every 100 tables.
    num_cols, num_rows, num_cells, col_types, cell_types, cell_column = __parse_table_stats(table_data)
    __write_stats(out_dir, num_cols, num_rows, num_cells, col_types, cell_types, cell_column)
    count += 10000
    print('Processed {:d} table stats so far...'.format(count))

    table_data.clear()


'''
    Write the statistics that we have gather for the KG.
'''


def __write_stats(out_dir, num_cols, num_rows, num_cells, col_types, cell_types, cell_column):
    num_cols_str = '\n'.join(map(str, num_cols))
    num_rows_str = '\n'.join(map(str, num_rows))
    num_cells_str = '\n'.join('{}\t{:d}'.format(v[0], v[1]) for v in list(num_cells.items()))

    col_types_str = '\n'.join('{}\t{}'.format(v[0], v[1]) for v in list(col_types.items()))
    cell_types_str = '\n'.join('{}\t{:d}'.format(v[0], v[1]) for v in list(cell_types.items()))

    cell_column_str = ''
    for cell_ in cell_column:
        cell_column_str += '\n'.join('{}\t{}\t{}\n'.format(cell_, v[0], v[1]) for v in list(cell_column[cell_].items()))

    fin = open(out_dir + '/num_columns_stats.tsv', 'a', encoding='utf_8')
    fin.write(num_cols_str + '\n')
    fin.close()

    fin = open(out_dir + '/num_rows_stats.tsv', 'a', encoding='utf_8')
    fin.write(num_rows_str + '\n')
    fin.close()

    fin = open(out_dir + '/num_cells_stats.tsv', 'a', encoding='utf_8')
    fin.write(num_cells_str + '\n')
    fin.close()

    fin = open(out_dir + '/col_types_stats.tsv', 'a', encoding='utf_8')
    fin.write(col_types_str + '\n')
    fin.close()

    fin = open(out_dir + '/cell_types_stats.tsv', 'a', encoding='utf_8')
    fin.write(cell_types_str + '\n')
    fin.close()

    fin = open(out_dir + '/cell_column_stats.tsv', 'a', encoding='utf_8')
    fin.write(cell_column_str + '\n')
    fin.close()


'''
    We gather different statistics for the KG that we have created.
'''


def __parse_table_stats(table_data):
    num_cols = []
    num_rows = []
    num_cells = {}

    col_types = {}
    cell_types = {}
    cell_column = {}

    for tbl_id in table_data:
        lines_ = table_data[tbl_id]
        num_cells[tbl_id] = 0

        cell_value_ = None
        for line in lines_:
            if 'tn:numberOfRows' in line:
                data = int(line[-2])
                num_rows.append(data)
            elif 'tn:numberOfColumns' in line:
                data = int(line[-2])
                num_cols.append(data)
            elif 'dct:subject' in line:
                type = line[-1]
                type = type[1:len(type) - 2]
                col_types[line[0]] = type
            elif 'tn:Cell' in line:
                num_cells[tbl_id] += 1
            elif 'tn:cellType' in line:
                cell_type_ = line[-2]
                if cell_type_ not in cell_types:
                    cell_types[cell_type_] = 1
                else:
                    cell_types[cell_type_] += 1

            # the last two clauses are necessary to store the cell-column value distributions.
            elif 'tn:cellValue' in line:
                cell_value_ = line[-2]
            elif 'tn:partOfColumn' in line:
                cell_column_ = line[-2]
                cell_column_ = cell_column_.split('_')[-1]

                # we store here the cell-column distributions
                if cell_value_ not in cell_column:
                    cell_column[cell_value_] = {}
                    cell_column[cell_value_][cell_column_] = 1
                else:
                    if cell_column_ not in cell_column[cell_value_]:
                        cell_column[cell_value_][cell_column_] = 1
                    else:
                        cell_column[cell_value_][cell_column_] += 1

    return num_cols, num_rows, num_cells, col_types, cell_types, cell_column


if __name__ == '__main__':
    arg = get_arguments()
    isFile = os.path.isfile(arg.input_kg_files)

    if not isFile:
        onlyfiles = [f for f in os.listdir(arg.input_kg_files) if isfile(join(arg.input_kg_files, f)) if 'wikitbls_kg_' in f]
        for file in onlyfiles:
            print('Parsing file {}'.format(file))
            if arg.stats_flag == 'a':
                __parse_kg_by_table(file, arg.out_dir)
            else:
                __num_triples_per_table(file, arg.out_dir)
    else:
        print('Parsing file {}'.format(arg.input_kg_files))
        if arg.stats_flag == 'a':
            __parse_kg_by_table(arg.input_kg_files, arg.out_dir)
        else:
            __num_triples_per_table(arg.input_kg_files, arg.out_dir)
