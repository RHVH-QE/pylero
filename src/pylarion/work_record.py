# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from pylarion.base_polarion import BasePolarion
from pylarion.enum_option_id import EnumOptionId
from pylarion.user import User


class WorkRecord(BasePolarion):
    """Object to handle the Polarion WSDL tns5:WorkRecord class

    Attributes (for specific details, see Polarion):
        comment (string)
        date (date)
        work_record_id (string)
        time_spent (duration)
        type (EnumOptionId)
        user (User)
"""
    _cls_suds_map = {"comment": "comment",
                     "date": "date",
                     "work_record_id": "id",
                     "time_spent": "timeSpent",
                     "type":
                     {"field_name": "type",
                      "cls": EnumOptionId,
                      "enum_id": "work-record-type"},
                     "user":
                     {"field_name": "user",
                      "cls": User},
                     "uri": "_uri",
                     "_unresolved": "_unresolved"}
    _obj_client = "builder_client"
    _obj_struct = "tns5:WorkRecord"


class ArrayOfWorkRecord(BasePolarion):
    _obj_client = "builder_client"
    _obj_struct = "tns5:ArrayOfWorkRecord"
