# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from pylarion.base_polarion import BasePolarion
from pylarion.text import Text


class Category(BasePolarion):
    """Object to handle the Polarion WSDL tns5:Category class

    Attributes (for specific details, see Polarion):
        description (Text)
        category_id (string)
        name (string)
"""
    _cls_suds_map = {"description":
                     {"field_name": "description",
                      "cls": Text},
                     "category_id": "id",
                     "name": "name",
                     "uri": "_uri",
                     "_unresolved": "_unresolved"}
    _obj_client = "builder_client"
    _obj_struct = "tns5:Category"
    _id_field = "category_id"


class ArrayOfCategory(BasePolarion):
    _obj_client = "builder_client"
    _obj_struct = "tns5:ArrayOfCategory"
