# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from pylarion.base_polarion import BasePolarion


class LicenseInfo(BasePolarion):
    """Object to handle the Polarion WSDL tns3:LicenseInfo class

    Attributes (for specific details, see Polarion):
        license (string)
        slots (int)
"""
    _cls_suds_map = {"license": "license",
                     "slots": "slots",
                     "uri": "_uri",
                     "_unresolved": "_unresolved"}
    _obj_client = "security_client"
    _obj_struct = "tns3:LicenseInfo"
