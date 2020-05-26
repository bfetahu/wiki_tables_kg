import gzip
import json
from operator import itemgetter
import random

from data_prep.cat_tax import CatTax
from data_prep.table import Table

'''
    Load the tables data.
'''

random.seed(10)


def load_tables(infile, start=0, limit=None, random_sample=False, tax=None, ecats=None):
    print('Loading tables from file {} with sampling {}'.format(infile, str(random_sample)))
    if infile.endswith('gz'):
        reader = gzip.open(infile, 'r')
    else:
        reader = open(infile, 'r')

    # read the tables data
    tables = {}
    count = 0
    loaded_tables = 0
    for line in reader:
        # parse the entity table json
        entity_json = json.loads(line.strip())
        entity_label = entity_json['entity']

        # iterate through the sections
        for section in entity_json['sections']:
            section_label = section['section']

            for table in section['tables']:
                count += 1
                if count < start:
                    continue

                loaded_tables += 1
                # do not load more than the set limit
                if limit is not None and loaded_tables > limit:
                    return tables

                tbl_obj = Table(flat_taxonomy=tax, ecats=ecats)
                tbl_obj.load_json(table, entity_label, section_label)

                tables[tbl_obj.table_id] = tbl_obj
    return tables


'''
   Load the parents of a category up to the root.
'''


def load_cat_parents(taxonomy, cat_name, parents, visited_cats):
    if cat_name not in taxonomy or cat_name in visited_cats:
        return

    cat = taxonomy[cat_name]
    parents.append((cat.name, cat.level))
    visited_cats.add(cat.name)

    for parent in cat.parents:
        load_cat_parents(taxonomy, parent.name, parents, visited_cats)


'''
    For a given set of entities return their common LCA category/type. 
    This is in a way representing the subject or class of the given entities.
'''


def find_lca_category(taxonomy, seed_entities, e_cats):
    if seed_entities is None or len(seed_entities) == 0:
        return []

    entity_tax_parents = {}
    for entity in seed_entities:
        if entity not in e_cats:
            continue
        entity_tax_parents[entity] = []
        visited_cats = set()
        for cat_name in e_cats[entity]:
            load_cat_parents(taxonomy, cat_name, entity_tax_parents[entity], visited_cats)

    # find the common categories
    common_cats = set()
    for idx, entity in enumerate(entity_tax_parents):
        if idx == 0:
            common_cats = set(entity_tax_parents[entity])
            continue
        common_cats.intersection(entity_tax_parents[entity])

    if len(common_cats) == 0:
        return []

    # get the lowest matching category
    if len(common_cats) != 0:
        val = max(common_cats, key=itemgetter(1))
        return [val[0]]

    return []


'''
    Load the category taxonomy where each node has contains its parents
'''


def load_flat_cat_tax(tax_path):
    taxonomy = {}

    for line in gzip.open(tax_path, 'rt', encoding='latin_1'):
        data = line.strip().lower().split('\t')

        cat_child = CatTax(data[2], int(data[3]))
        cat_parent = CatTax(data[0], int(data[1]))

        if cat_child.name not in taxonomy:
            taxonomy[cat_child.name] = cat_child
            cat_child.add_parent(cat_parent)
        else:
            taxonomy[cat_child.name].add_parent(cat_parent)
    return taxonomy


'''
    Loads the entity categories.
'''


def load_entity_cats(ec_path):
    entity_cats = {}
    for line in gzip.open(ec_path, 'rt', encoding='latin_1'):
        data = line.strip().lower().split('\t')
        if len(data) != 2:
            continue

        if data[0] not in entity_cats:
            entity_cats[data[0]] = []
        entity_cats[data[0]].append(data[1])
    return entity_cats
