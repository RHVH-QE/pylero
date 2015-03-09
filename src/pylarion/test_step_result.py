# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from pylarion.base_polarion import BasePolarion
from pylarion.test_run_attachment import TestRunAttachment
from pylarion.test_run_attachment import ArrayOfTestRunAttachment
from pylarion.text import Text
from pylarion.enum_option_id import EnumOptionId


class TestStepResult(BasePolarion):
    """Object to handle the Polarion WSDL tns3:TestStepResult class

    Attributes (for specific details, see Polarion):
        attachments (ArrayOfTestRunAttachment)
        comment (Text)
        result (EnumOptionId)
"""
    _cls_suds_map = {"attachments":
                     {"field_name": "attachments",
                      "is_array": True,
                      "cls": TestRunAttachment,
                      "arr_cls": ArrayOfTestRunAttachment,
                      "inner_field_name": "TestRunAttachment"},
                     "comment":
                     {"field_name": "comment",
                      "cls": Text},
                     "result":
                     {"field_name": "result",
                      "cls": EnumOptionId},
                     "uri": "_uri",
                     "_unresolved": "_unresolved"}
    _obj_client = "test_management_client"
    _obj_struct = "tns3:TestStepResult"


class ArrayOfTestStepResult(BasePolarion):
    _obj_client = "test_management_client"
    _obj_struct = "tns3:ArrayOfTestStepResult"
