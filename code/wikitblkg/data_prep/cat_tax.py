class CatTax:
    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.parents = set()

    def add_parent(self, cat_parent):
        self.parents.add(cat_parent)