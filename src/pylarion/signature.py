# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from pylarion.base_polarion import BasePolarion
from pylarion.enum_option_id import EnumOptionId
from pylarion.user import User


class Signature(BasePolarion):
    _cls_suds_map = {"verdict":
                     {"field_name": "verdict",
                      "cls": EnumOptionId},
                     "signed_revision": "signedRevision",
                     "verdict_time": "verdictTime",
                     "signer_role": "signerRole",
                     "signed_by":
                     {"field_name": "signedBy",
                      "cls": User}}
    _obj_client = "test_management_client"
    _obj_struct = "tns4:Signature"


class ArrayOfSignature(BasePolarion):
    _obj_client = "test_management_client"
    _obj_struct = "tns4:ArrayOfSignature"
