# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from pylarion.base_polarion import BasePolarion
from pylarion.enum_option_id import EnumOptionId


class Hyperlink(BasePolarion):
    """Object to handle the Polarion WSDL tns5:Hyperlink class

    Attributes (for specific details, see Polarion):
        role (EnumOptionId)
        uri (string)
"""
    _cls_suds_map = {"role":
                     {"field_name": "role",
                      "cls": EnumOptionId},
                     "uri": "uri",
                     "uri": "_uri",
                     "_unresolved": "_unresolved"}
    _obj_client = "builder_client"
    _obj_struct = "tns5:Hyperlink"


class ArrayOfHyperlink(BasePolarion):
    _obj_client = "builder_client"
    _obj_struct = "tns5:ArrayOfHyperlink"
