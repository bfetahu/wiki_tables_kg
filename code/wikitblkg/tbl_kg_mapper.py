'''
    In this class we define the mapping procedure for a table into the WikiTblKG schema.
'''

import json
import re
from urllib.parse import quote_plus


class Tbl2KgMapper:
    def __init__(self, tables, out_dir, is_light=False, suffix='part_1'):
        self.tables = tables
        self.out_dir = out_dir
        self.is_light = is_light
        self.suffix = suffix

    def write_tables(self):
        # iterate over all tables and generate the content.
        fout = open(self.out_dir + '/wikitbls_kg_' + self.suffix + '.nt', 'wt')
        out = ''

        for table_id in self.tables:
            table = self.tables[table_id]
            out += self.map_table_to_resource(table)
            if len(out) > 100000:
                fout.write(out)
                out = ''

        fout.write(out)
        fout.flush()
        fout.close()
        print('Finished writing all the data into the knowledge graph.')

    '''
        Map a table in JSON format to its RDF representation according to the WikiTablesKG schema.
    '''

    def map_table_to_resource(self, table):
        tbl_uri = '<http://www.tablenet.l3s.uni-hannover.de/TableNet#{:d}>'.format(table.table_id)
        tbl_uri_json_raw = '<http://www.tablenet.l3s.uni-hannover.de/TableNet/json/{:d}>'.format(table.table_id)

        # add table metadata
        out_meta = self.__add_table_metadata(table=table, table_URI=tbl_uri, table_URI_json_raw=tbl_uri_json_raw)

        # add the column information.
        out_col, columns = self.__add_table_columns(table=table, table_URI=tbl_uri)

        # add the row information.
        out_row = ''
        if not self.is_light:
            out_row = self.__add_row_data(table=table, table_URI=tbl_uri, columns=columns)

        tbl_out = out_meta + out_col + out_row
        return tbl_out

    '''
        Add the metadata data about the table, which includes the number of rows, columns, access to the raw content etc.
    '''

    def __add_table_metadata(self, table, table_URI, table_URI_json_raw):
        out = '{} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://www.tablenet.l3s.uni-hannover.de/TableNet#Table> .\n'.format(table_URI)

        out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#hasTableID> {:d} .\n'.format(table_URI, table.table_id)
        out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#numberOfColumns> {:d} .\n'.format(table_URI, table.num_cols)
        out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#numberOfRows> {:d} .\n'.format(table_URI, len(table.table_rows))

        if len(table.table_caption):
            caption = table.table_caption
            caption = caption.replace('"', '')

            out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#hasCaption> "{}" .\n'.format(table_URI, caption)

        section = '' if table.section == 'MAIN_SECTION' else table.section

        entity = re.sub(' ', '_', table.entity)
        section = re.sub(' ', '_', section)

        doc_source_section_URI = quote_plus('{}#{}'.format(entity, section))
        doc_source_URI = quote_plus('{}'.format(entity))

        out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#document> <http://en.wikipedia.org/wiki/{}> .\n'.format(table_URI, doc_source_section_URI)
        out += '{} <http://purl.org/dc/terms/source> <http://dbepdia.org/resource/{}> .\n'.format(table_URI, doc_source_URI)
        out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#resourceURL> {} .\n'.format(table_URI, table_URI_json_raw)

        # if not self.is_light:
        #     out += '{} {}:rawJSON "{}" .\n'.format(table_URI, self.schema_prefix, json.dumps(table.table_json))

        return out

    '''
        Add the column information.
    '''

    def __add_table_columns(self, table, table_URI):
        out = ''
        columns = {}
        for col_level in range(len(table.columns)):
            columns_ = table.columns[col_level]
            for col_idx, column in enumerate(columns_):
                column_ = column.replace('"', '\'\'')
                col_uri_base = quote_plus(re.sub(' ', '_', column_))

                col_URI = '<https://www.tablenet.l3s.uni-hannover.de/TableNet#{:d}_{:d}_{}>'.format(table.table_id, col_level, col_uri_base)
                out += '{} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.tablenet.l3s.uni-hannover.de/TableNet#Column> .\n'.format(col_URI)
                out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#columnPosition> {:d} .\n'.format(col_URI, col_idx)
                out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#hasLevel> {:d} .\n'.format(col_URI, col_level)
                out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#columnName> "{}" .\n'.format(col_URI, column_)

                # here we only assign types to columns that are of the lowest level, otherwise we mark it as NA
                if col_level == len(table.columns) - 1:
                    col_type = table.column_types[column].replace('"', '\'\'')
                    col_type_quoted = quote_plus(re.sub(' ', '_', col_type))
                    out += '{} <http://purl.org/dc/terms/subject> "{}" .\n'.format(col_URI, col_type_quoted)
                else:
                    out += '{} <http://purl.org/dc/terms/subject> "N/A" .\n'.format(col_URI)

                out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#hasColumn> {} .\n'.format(table_URI, col_URI)

                # add the column data for later use, we store only the last layer
                if col_level == len(table.columns) - 1:
                    columns[column] = col_URI
        return out, columns

    '''
        Add the row data. We add the different rows, and for each row we add cell values which correspondingly have a column assigned to them.
    '''

    def __add_row_data(self, table, table_URI, columns):
        out = ''
        # print (columns)
        cell_counter = 0
        for row_idx, row in enumerate(table.table_rows):
            row_URI = '_:r{:d}_{:d}'.format(table.table_id, row_idx)

            out += '{} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://www.tablenet.l3s.uni-hannover.de/TableNet#Row> .\n'.format(row_URI)
            out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#rowPosition> {:d} .\n'.format(row_URI, row_idx)
            out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#hasRow> {} .\n'.format(table_URI, row_URI)

            # add the cell values to the row
            for column in row.keys():
                cell_type, cell_extracted_val, cell_val = row[column]

                col_URI = columns[column]
                cell_URI = '_:c{:d}_{:d}'.format(table.table_id, cell_counter)
                out += '{} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://www.tablenet.l3s.uni-hannover.de/TableNet#Cell> .\n'.format(cell_URI)

                if cell_type == 'STRUCT':
                    for val_ in cell_extracted_val:
                        if len(val_):
                            val_tmp = val_.replace('"', '\'\'')
                            cell_struct_URI = quote_plus('{}'.format(re.sub(' ', '_', val_tmp)))

                            out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#cellValue> <http://en.wikipedia.org/wiki/{}> .\n'.format(cell_URI, cell_struct_URI)
                            out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#refersTo> <http://dbpedia.org/resource/{}> .\n'.format(cell_URI, cell_struct_URI)
                else:
                    cell_val_ = cell_val.replace('"', '\'\'')
                    cell_val_escaped = quote_plus('{}'.format(re.sub(' ', '_', cell_val_)))
                    out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#cellValue> "{}" .\n'.format(cell_URI, cell_val_escaped)

                out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#cellType> "{}" .\n'.format(cell_URI, cell_type)

                out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#partOfColumn> {} .\n'.format(cell_URI, col_URI)
                out += '{} <https://www.tablenet.l3s.uni-hannover.de/TableNet#hasCell> {} .\n'.format(row_URI, cell_URI)
                cell_counter += 1

        return out
