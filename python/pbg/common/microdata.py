"""Thin wrapper around the microdata library."""
from __future__ import absolute_import
import microdata


class Item(microdata.Item):
    """Add an "extra" field to microdata Items, so people won't feel the need
    to make up ad-hoc properties."""

    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)

        self.extra = {}

    def json_dict(self):
        item = super(Item, self).json_dict()

        if self.extra:
            item['extra'] = self.extra

        return item
