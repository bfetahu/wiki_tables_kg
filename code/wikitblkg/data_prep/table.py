import re
from collections import defaultdict

import data_utils as du


class Table:
    def __init__(self, flat_taxonomy, ecats):
        self.table_rows = []
        self.columns = []
        self.table_caption = ''
        self.entity = ''
        self.section = ''
        self.label = 'NA'
        self.table_html = ''
        self.table_json = ''
        self.table_id = -1
        self.num_cols = -1

        # we use these to determine the column types
        self.flat_taxonomy = flat_taxonomy
        self.ecats = ecats

        # here we keep the value distribution for a column
        self.column_meta_data = defaultdict(list)

        # here we keep the cell values for columns and distinguish if they are literals or instances (based on the links)
        self.column_cell_value_data = defaultdict(list)

        # keep the column types here
        self.column_types = {}

    '''
        Set the type of the columns either STRUCT or LITERAL. The column can either have instance values or literals.
        NOTE: We do not look for all values belonging to one class, but if at least one value is an instance then the column is STRUCT.
    '''

    def __set_column_types(self):
        # we only consider the last layer of columns.
        columns_ = self.columns[-1]
        for column in columns_:
            if column not in self.column_cell_value_data:
                self.column_types[column] = 'LITERAL'
            else:
                vals_ = [v_[-1] for v_ in self.column_cell_value_data[column] if v_[0] == 'STRUCT']
                if len(vals_) == 0:
                    self.column_types[column] = 'LITERAL'
                else:
                    lca = du.find_lca_category(self.flat_taxonomy, vals_, self.ecats)
                    self.column_types[column] = 'N/A' if len(lca) == 0 else lca[0]

    '''
        Load the table from the json dump.
    '''

    def load_json(self, table_json, entity, section):
        self.entity = entity
        self.section = section
        self.table_json = table_json

        self.__parse_table_data()
        self.__set_column_types()

        self.table_json = ''

    '''
        Add the column names to the table column schema.
    '''

    def __add_column_names(self):
        header = self.table_json['header']
        # header = header[len(header) - 1]['columns']

        for i in range(len(header)):
            header_ = header[i]['columns']
            cols_ = []
            for col in header_:
                col_name = self.__parse_column_name(col['name'])
                # values = col['value_dist']

                cols_.append(col_name)
                # self.columns.append(col_name)
                # for value in values:
                #     self.column_meta_data[col_name].append((value['value'], value['count']))
            self.columns.append(cols_)

        # number of columns in the last layer.
        self.num_cols = len(cols_)

    '''
        Remove white spaces and some reserved characters such that it is RDF compliant.
    '''

    def __parse_column_name(self, col_name):
        col_name = re.sub('#', 'nr', re.sub(' ', '_', col_name.strip()))
        col_name = re.sub('\(', '\\(', re.sub(' ', '_', col_name))
        col_name = re.sub('\)', '\\)', re.sub(' ', '_', col_name))
        col_name = re.sub('\{', '\\{', re.sub(' ', '_', col_name))
        col_name = re.sub('\}', '\\}', re.sub(' ', '_', col_name))
        col_name = re.sub('\[', '\\[', re.sub(' ', '_', col_name))
        col_name = re.sub('\]', '\\]', re.sub(' ', '_', col_name))
        return col_name

    '''
        Process the table HTML into the different sub-parts: (1) table caption, (2) table header (columns), (3) table cells
    '''

    def __parse_table_data(self):
        # first check if the table has a caption
        self.table_id = self.table_json['id']
        self.table_caption = self.table_json['caption']

        # load the column meta data
        self.__add_column_names()

        # get the table header and process it into the different rows and columns
        for idx, row in enumerate(self.table_json['rows']):
            row_cell_dict = dict()
            for cell in row['values']:
                col_idx = cell['col_index']
                if col_idx >= self.num_cols:
                    col_idx = self.num_cols - 1
                    print('{:d} col index out of {:d} columns'.format(col_idx, self.num_cols))
                    # print (self.table_json)

                col_name = self.columns[-1][col_idx]
                # parse the cell value and see what type of value we are dealing with
                cell_val_ = self.__parse_cell_value(cell)
                row_cell_dict[col_name] = cell_val_
            self.table_rows.append(row_cell_dict)

    '''
        Parse the cell value by checking if the value points to an instance/entity or it is simply a literal.
    '''

    def __parse_cell_value(self, cell):
        col_name = self.__parse_column_name(cell['column'])

        if 'structured_values' in cell:
            vals_ = []
            for struct_val in cell['structured_values']:
                vals_.append(struct_val['structured'])
                self.column_cell_value_data[col_name].append(('STRUCT', struct_val['structured']))
            return ('STRUCT', vals_, struct_val['anchor'])
        else:
            self.column_cell_value_data[col_name].append(('LIT', cell['value']))
            return ('LIT', cell['value'], cell['value'])
