"""Thin wrapper around the microdata library."""
from __future__ import absolute_import
import microdata


class Item(microdata.Item):
    """Add an "extra" field to microdata Items, so people won't feel the need
    to make up ad-hoc properties.

    Also add __eq__() and __repr__().
    """

    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)

        self.extra = {}

    def json_dict(self):
        item = super(Item, self).json_dict()

        if self.extra:
            item['extra'] = self.extra

        return item

    def __eq__(self, other):
        if not isinstance(other, microdata.Item):
            return False

        return (self.itemid == other.itemid and
                self.itemtype == other.itemtype and
                self.props == other.props and
                self.extra == getattr(other, 'extra', {}))

    def __repr__(self):
        return '%s(%r, %r, props=%r, extra=%r)' % (
            self.__class__.__name__,
           ' '.join(uri.string for uri in self.itemtype),
           self.itemid,
           self.props,
           self.extra)
