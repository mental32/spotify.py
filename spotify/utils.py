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
