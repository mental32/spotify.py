##
# -*- coding: utf-8 -*-
##

def find(predicate, seq):
    for element in seq:
        if predicate(element):
            return element
    return None

def get(iterable, **attrs):
    def predicate(elem):
        for attr, val in attrs.items():
            nested = attr.split('__')
            obj = elem
            for attribute in nested:
                obj = getattr(obj, attribute)

            if obj != val:
                return False
        return True

    return find(predicate, iterable)


def _filter_options(**kwargs):
    payload = {}
    for key, value in kwargs.items():
        if value is not None:
            payload[key] = value
    else:
        return payload


def _unique_cache(lst, item):
    for index, obj in enumerate(lst):
        if hasattr(obj, 'id'):
            if obj.id == item.id:
                lst[index] = item


def ensure_http(self):
    if not hasattr(self, 'http'):
        raise AttributeError('type obj %s has no attribute \'http\': To perform API requests User needs a HTTP presence.' %(type(self)))
