# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals
import os
import suds
import datetime
from xml.dom import minidom
from pylarion.exceptions import PylarionLibException
from pylarion.base_polarion import BasePolarion
from pylarion.test_run_attachment import TestRunAttachment
from pylarion.test_run_attachment import ArrayOfTestRunAttachment
from pylarion.enum_option_id import EnumOptionId
from pylarion.test_record import TestRecord
from pylarion.test_record import ArrayOfTestRecord
from pylarion.custom import Custom
from pylarion.custom import ArrayOfCustom
from pylarion.document import Document
from pylarion.work_item import _WorkItem
from pylarion.user import User
from pylarion.project import Project
from pylarion.text import Text
# Plan is used in custom fields.
from pylarion.plan import Plan  # NOQA
from pylarion.base_polarion import tx_wrapper
import requests
from requests.auth import HTTPBasicAuth


class TestRun(BasePolarion):
    """Object to manage the Polarion Test Management WS tns3:TestRun

    Attributes:
        attachments (list of TestRunAttachments)
        author (User): user object of the Test Run Author
        created (datetime)
        document (Module)
        finished_on (datetime)
        group_id
        is_template (bool): indicates if the TestRun object is a Template
        keep_in_history (bool)
        location
        project (Project)
        query (str): The Polarion query that the TestRun objects are based on.
        records (list of TestRecord objects)
        select_test_cases_by (EnumOptionId):
            The test cases can be:
                AUTOMATED_PROCESS
                DYNAMIC_QUERY
                DYNAMIC_LIVEDOC
                MANUAL_SELECTION
                STATIC_QUERY
                STATIC_LIVEDOC

        status
        summary_defect (_WorkItem)
        template (TestRun): template that the TestRun is based on.
        test_run_id (str): Unique identifier of the test run within the
                           project
        type
        updated
        custom_fields
    """
    _cls_suds_map = {
        "attachments":
            {"field_name": "attachments",
             "is_array": True,
             "cls": TestRunAttachment,
             "arr_cls": ArrayOfTestRunAttachment,
             "inner_field_name": "TestRunAttachment"},
        "author":
            {"field_name": "authorURI",
             "cls": User,
             "named_arg": "uri",
             "sync_field": "uri"},
        "created": "created",
        "document":
            {"field_name": "document",
             "cls": Document},
        "finished_on": "finishedOn",
        "group_id": "groupId",
        "test_run_id": "id",
        "is_template": "isTemplate",
        "keep_in_history": "keepInHistory",
        "location": "location",
        "project_id":
            {"field_name": "projectURI",
             "cls": Project,
             "named_arg": "uri",
             "sync_field": "uri"},
        "query": "query",
        "_records":
            {"field_name": "records",
             "is_array": True,
             "cls": TestRecord,
             "arr_cls": ArrayOfTestRecord,
             "inner_field_name": "TestRecord"},
        "select_test_cases_by":
            {"field_name": "selectTestCasesBy",
             "cls": EnumOptionId,
             "enum_id": "testrun-selectTestCasesBy"},
        "status":
            {"field_name": "status",
             "cls": EnumOptionId,
             "enum_id": "testing/testrun-status"},
        "summary_defect":
            {"field_name": "summaryDefectURI",
             "cls": _WorkItem,
             "named_arg": "uri",
             "sync_field": "uri"},
        "template":
            {"field_name": "templateURI",
             "named_arg": "uri",
             "sync_field": "uri"},
        "type":
            {"field_name": "type",
             "cls": EnumOptionId,
             "enum_id": "testing/testrun-type"},
        "updated": "updated",
        # the custom field attribute has been changed to be a protected attr.
        # All interaction with custom fields should be done directly with the
        # derived attribute.
        "_custom_fields":
            {"field_name": "customFields",
             "is_array": True,
             "cls": Custom,
             "arr_cls": ArrayOfCustom,
             "inner_field_name": "Custom"},
        "uri": "_uri",
        "_unresolvable": "_unresolvable"}
    _id_field = "test_run_id"
    _obj_client = "test_management_client"
    _obj_struct = "tns3:TestRun"
    CUSTOM_FIELDS_FILE = \
        ".polarion/testing/configuration/testrun-custom-fields.xml"
    _custom_field_cache = {}

    @property
    def records(self):
        """ function to return all the test records of a TestRun.
        The records array for dynamic queries/documents only includes executed
        records. This returns the unexecuted ones as well.

        Args:
            None

        Returns:
            list of TestRecords
        """
        self._verify_obj()
        contained_cases = ["static", "manual"]
        if any(s in self.select_test_cases_by for s in contained_cases):
            return self._records
        if "Doc" in self.select_test_cases_by:
            cases = self.document.get_work_items(None, True)
        elif "Query" in self.select_test_cases_by:
            cases = _WorkItem.query(
                self.query + " AND project.id:" + self.project_id)
        executed_ids = [rec.test_case_id for rec in self._records]
        test_recs = self._records
        for case in cases:
            if case.work_item_id not in executed_ids \
                    and case.type != "heading":
                test_recs.append(
                    TestRecord(self.project_id, case.work_item_id))
        return test_recs

    @records.setter
    def records(self, val):
        self._records = val

    @classmethod
    def create(cls, project_id, test_run_id, template):
        """class method create for creating a new test run in Polarion

        Args:
            project_id (string): the Polarion project to create the test run
                                 in
            test_run_id (string): the unique identifier for the test run
            template (string): the id of the template to base the test run on.

        Returns:
            The created TestRun object

        References:
            test_management.createTestRun
        """
        uri = cls.session.test_management_client.service.createTestRun(
            project_id, test_run_id, template)
        if uri:
            return cls(uri=uri)
        else:
            raise PylarionLibException("Test Run was not created")

    @classmethod
    @tx_wrapper
    def create_template(cls, project_id, template_id,
                        parent_template_id="Empty",
                        select_test_cases_by=None, query=None,
                        doc_with_space=None):  # , test_case_ids=[]):
        # see comment below regarding test_case)ids.
        """class method create_template for creating a new template in Polarion

        Args:
            project_id (string): the Polarion project to create the test run
                                 in
            template_id (string): the unique identifier for the template
            parent_template_id: the template that this is based on
                                Default: "Empty"
            select_test_cases_by: the method used to choose test cases
                                  NOTE: It is currently not possible to select
                                  test cases manually via the API.
                                  Default: None
            query: the Lucene query, for query methods, default None
            doc_with_space: the space/doc_name, for document methods
                            default: None

        Returns:
            The created TestRun Template object

        References:
            test_management.createTestRun
        """
        tr = cls.create(project_id, template_id, parent_template_id)
        tr.is_template = True
        if select_test_cases_by:
            tr.select_test_cases_by = select_test_cases_by
        elif doc_with_space:
            tr.select_test_cases_by = "dynamicLiveDoc"
        elif query:
            tr.select_test_cases_by = "dynamicQueryResult"

        if query:
            tr.query = query
        elif doc_with_space:
            tr.document = Document(project_id, doc_with_space)
# TODO: This should work as soon as Polarion implements Change Request REQ-6334
#        if test_case_ids:
#            for test_case_id in test_case_ids:
#                tr.add_test_record_by_object(testrec.TestRecord(
#                                             test_case_id, project_id))

        tr.update()
        return TestRun(template_id, project_id=project_id)

    @classmethod
    def search(cls, query, fields=[], sort="test_run_id", limit=-1,
               search_templates=False):
        """class method search executes the given query and returns the results

        Args:
            query: the Polarion query used to find test runs
            fields:  test run fields that should be initialized,
                     all other fields will be null.
                     Field names are from the object's attributes and not
                     the Polarion field names, default []
            sort: the field used to sort results, default is test_run_id
            limit (int): the maximum number of records to be returned, -1
                         for no limit, default -1.
            search_templates (bool): if set, searches the templates
                                     instead of the test runs, default False
        Returns:
            list of TestRun objects

        References:
            test_management.searchTestRunTemplates
            test_management.searchTestRunTemplatesLimited
            test_management.searchTestRunTemplatesWithFields
            test_management.searchTestRunTemplatesWithFieldsLimited
            test_management.searchTestRuns
            test_management.searchTestRunLimited
            test_management.searchTestRunsWithFields
            test_management.searchTestRunsWithFieldsLimited
        """
# The Polarion functions with limited seem to be the same as without limited
#    when -1 is passed in as limit. Because of this, the wrapper will not
#    implement the functions without limited.
        function_name = "search"
        p_sort = cls._cls_suds_map[sort] if not isinstance(
            cls._cls_suds_map[sort], dict) else \
            cls._cls_suds_map[sort]["field_name"]
        parms = [query, p_sort]
        if search_templates:
            function_name += "TestRunTemplates"
        else:
            function_name += "TestRuns"
        p_fields = cls._convert_obj_fields_to_polarion(fields)
        if p_fields:
            function_name += "WithFieldsLimited"
            parms.append(p_fields)
        parms.append(limit)
        test_runs = []
        results = getattr(cls.session.test_management_client.service,
                          function_name)(*parms)
        for suds_obj in results:
            tr = TestRun(suds_object=suds_obj)
            test_runs.append(tr)
        return test_runs

    def __init__(self, test_run_id=None, suds_object=None, project_id=None,
                 uri=None):
        """TestRun constructor.

        Args:
            test_run_id: when given, the object is populated with the
                         TestRuns. Requires project_id parameter
            suds_object: Polarion TestRun object. When given, the object
                         is populated by object data.
            project_id: the Polarion project that the Test Run is located
                        in. Required if test_run_id is passed in
            uri: the uri that references the Polarion TestRun

        Notes:
            Either test_run_id and project or suds_object or uri can be passed
            in or none of them. If none of the identifying parameters are
            passed in an empty object is created

        References:
            test_management.getTestRunById
            test_management.getTestRunByUri
        """
        self._add_custom_fields(project_id)
        super(self.__class__, self).__init__(test_run_id, suds_object)
        if test_run_id:
            if not project_id:
                raise PylarionLibException("When test_run_id is passed in, "
                                           "project_id is required")
            self._suds_object = self.session.test_management_client.service. \
                getTestRunById(project_id, test_run_id)
        elif uri:
            self._suds_object = self.session.test_management_client.service. \
                getTestRunByUri(uri)
        if test_run_id or uri:
            if getattr(self._suds_object, "_unresolvable", True):
                raise PylarionLibException(
                    "The Test Run {0} was not found.".format(test_run_id))

    def _fix_circular_refs(self):
        # a class can't reference itself as a class attribute so it is
        # defined after instatiation
        self._cls_suds_map["template"]["cls"] = self.__class__

    def _custom_field_types(self, field_type):
        """There are 4 types of custom fields in test runs:
        * built-in types (string, boolean, ...)
        * Pylarion Text object (text)
        * Enum of existing type (@ prefix, i.e. enum:@user = Pylarion User)
        * Enum, based on lookup table(i.e. enum:arch)
        The basic enums can get their valid values using the BasePolarion
        get_valid_field_values function.
        The existing type Enums, must validate by instantiating the object.

        Args;
            field_type - the field type passed in from the custom xml file
        Returns:
            None for base types, Text class for text types, the object to
            validate the enum for Enum objects or the key to validate the enum
            for basic enums
        """
        if field_type == "text":
            return Text
        # some custom types have a [] segment. Still unsure of how to handle
        # those specific attributes, but for now, this will ignore them
        split_type = field_type.split("[")[0].split(":")
        if len(split_type) == 1:
            # a base type
            return None
        else:
            # an enum
            if split_type[1].startswith("@"):
                # an enum based on an object
                return [globals()[x] for x in globals()
                        if x.lower() == split_type[1][1:].lower()][0]
            else:
                # a regular enum
                return split_type[1]

    def _cache_custom_fields(self, project_id):
        """Polarion API does not provide the custom fields of a TestRun.
        As a workaround, this function connects to the SVN repo and reads the
        custom_fields xml file and then processes it. Because the SVN function
        takes longer then desired, this caches the custom fields, per project

        Args:
            project_id
        Returns
            None
        """
        proj = Project(project_id)
        # proj.location[8:-30] removes the default: at the beginning and
        # .polarion/polarion-project.xml
        file_download = requests.get("{0}{1}{2}".format(
            self.repo, proj.location[8:-30], self.CUSTOM_FIELDS_FILE),
            auth=HTTPBasicAuth(self.logged_in_user_id, self.session.password),
            verify=False)
        file_content = file_download.text
        xmldoc = minidom.parseString(file_content)
        fields = xmldoc.getElementsByTagName("field")
        self._custom_field_cache[project_id] = {}
        for field in fields:
            f_type = self._custom_field_types(field.getAttribute("type"))
            f_name = field.getAttribute("id")
            self._custom_field_cache[project_id][f_name] = f_type

    def _add_custom_fields(self, project_id):
        """ This generates object attributes, with validation, so that custom
        fields can be related to as regular attributes. It takes the custom
        fields from the cache and calls the cache function if the values are
        not already there.
        Args:
            project_id - Each project can have its own custom fields. This
                function takes the custom fields for the specific project and
                adds them to the _cls_suds_map so they will be built into
                object attributes.
        Returns:
            None
        """
        self._changed_fields = {}
        # force the session to initialize. This is needed here because the
        # system has not yet been initialized.
        self.session
        if not project_id:
            project_id = self.default_project
        if project_id not in self._custom_field_cache:
            self._cache_custom_fields(project_id)
        cache = self._custom_field_cache[project_id]
        for field in cache:
            self._cls_suds_map[field] = {}
            self._cls_suds_map[field]["field_name"] = field
            self._cls_suds_map[field]["is_custom"] = True
            if cache[field] == Text:
                self._cls_suds_map[field]["cls"] = Text
            elif cache[field]:
                self._cls_suds_map[field]["cls"] = EnumOptionId
                self._cls_suds_map[field]["enum_id"] = cache[field]
                if isinstance(cache[field], type) and \
                    "project_id" in \
                        cache[field].__init__.func_code.co_varnames[
                        :cache[field].__init__.func_code.co_argcount]:
                    self._cls_suds_map[field]["additional_parms"] = \
                        {"project_id": project_id}

    def _get_index_of_test_record(self, test_case_id):
        # specific functions request the index of the test record within the
        # test run. However, the user doesn't know what the index is.
        # Therefore the user passes in the test case id and this function
        # figures out the index.
        # However, this function does not work for update_test_record_by_object
        # as that function requires the actual index of the record and not the
        # index of only executed records.
        index = -1
        for test_record in self._records:
            if test_record.executed:
                index += 1
            if test_case_id in test_record._suds_object.testCaseURI:
                return index
        raise PylarionLibException("The Test Case is either not part of "
                                   "this TestRun or has not been executed")

    def _status_change(self):
        # load a new object to test if the status should be changed.
        # can't use existing object because it doesn't include the new test rec
        # if the status needs changing, change it in the new object, so it
        # doesn't update any user made changes in the existing object.
        check_tr = TestRun(uri=self.uri)
        results = [rec.result for rec in check_tr.records if rec.result]
        if not results:
            status = "notrun"
            check_tr.finished_on = None
        elif len(results) == len(check_tr.records):
            status = "finished"
            check_tr.finished_on = datetime.datetime.now()
        else:
            status = "inprogress"
            check_tr.finished_on = None
        if status != check_tr.status:
            check_tr.status = status
            check_tr.update()

    def _verify_record_count(self, record_index):
        # verifies the number of records is not less then the index given.
        self._verify_obj()
        if record_index > len(self.records)-1:
            raise PylarionLibException("There are only {0} test records".
                                       format(len(self.records)))

    def _verify_test_step_count(self, record_index, test_step_index):
        # verifies the number of test steps is not less then the index given.
        self._verify_record_count(record_index)
        if test_step_index > len(self.records[record_index].
                                 test_step_results)-1:
            raise PylarionLibException("There are only {0} test records".
                                       format(len(self.records)))

    def add_attachment_to_test_record(self, test_case_id, path, title):
        """method add_attachment_to_test_record, adds the given attachment to
        the specified test record

        Args:
            test_case_id (str): The id of the test case
            path: file path to upload
            title: u.User friendly name of the file

        Returns:
            None

        Notes:
            Raises an error if the test case given is not in the TestRun or has
            not been executed yet.

        References:
            test_management.addAttachmentToTestRecord
        """
        record_index = self._get_index_of_test_record(test_case_id)
        self._verify_record_count(record_index)
        data = self._get_file_data(path)
        filename = os.path.basename(path)
        self.session.test_management_client.service. \
            addAttachmentToTestRecord(self.uri, record_index, filename,
                                      title, data)

    def add_attachment(self, path, title):
        """method add_attachment adds the given attachment to the current
        test run

        Args:
            path: file path to upload
            title: u.User friendly name of the file

        Returns:
            None

        Notes:
            Raises an error if the test run object is not populated

        References:
            test_management.addAttachmentToTestRun
        """
        self._verify_obj()
        data = self._get_file_data(path)
        filename = os.path.basename(path)
        self.session.test_management_client.service. \
            addAttachmentToTestRun(self.uri, filename, title, data)

    def add_attachment_to_test_step(self, test_case_id, test_step_index,
                                    path, title):
        """method add_attachment_to_test_step, adds the given attachment to
        the specified test step of the specified test record

        Args:
            test_case_id (str): The id of the test case to the step is in
            test_step_index (int): The 0 based index of the test step
            path: file path to upload
            title: u.User friendly name of the file

        Returns:
            none

        Notes:
            Raises an error if the record_index given is higher then the number
            of test records. or if the test_step_index is higher then the
            number of steps.

        References:
            test_management.addAttachmentToTestStep
        """
        record_index = self._get_index_of_test_record(test_case_id)
        self._verify_test_step_count(record_index, test_step_index)
        data = self._get_file_data(path)
        filename = os.path.basename(path)
        self.session.test_management_client.service.addAttachmentToTestStep(
            self.uri, record_index, test_step_index, filename, title, data)

    def _check_test_record_exists(self, test_case_id):
        """Grabs a copy of the test run to verify if the test case is already
        contained in it. It uses a copy to get an updated version so that if
        it was added during the session, it will still appear.
        If it appears, it will raise an exception.

        Args:
            test_case_id (str): the id of the test case to check

        Returns:
            None
        """
        """
        :param test_case_id:
        :return:
        """
        check_tr = TestRun(uri=self.uri)
        if any(test_case_id == rec.test_case_id for rec in check_tr._records):
            raise PylarionLibException(
                "This test case is already part of the test run")

    @tx_wrapper
    def add_test_record_by_fields(self, test_case_id, test_result,
                                  test_comment, executed_by, executed,
                                  duration, defect_work_item_id=None):
        """method add_test_record_by_fields, adds a test record for the given
        test case based on the result fields passed in.
        When a test record is added, it changes the test run status to
        "inprogress" and when the last test record is run, it changes the
        status to done.

        Args:
            test_case_id (str): The id of the test case that was executed
            test_result (str): Must be one of the following values:
                                  passed
                                  failed
                                  blocked
            test_comment (str or Text object): may be None
            executed_by (str): user id
            executed (datetime):
            duration (float):
            defect_work_item_id (str): _WorkItem id of defect, default: None

        Returns:
            None

        References:
            test_management.addTestRecord
        """
        self._verify_obj()
        if not executed or not test_result:
            raise PylarionLibException(
                "executed and test_result require values")
        self._check_test_record_exists(test_case_id)
        self.check_valid_field_values(test_result, "result", {})
        tc = _WorkItem(work_item_id=test_case_id,
                       project_id=self.project_id,
                       fields=["work_item_id"])
        if test_comment:
            if isinstance(test_comment, basestring):
                obj_comment = Text(test_comment)
                suds_comment = obj_comment._suds_object
            elif isinstance(test_comment, Text):
                suds_comment = test_comment._suds_object
            else:  # is a suds object
                suds_comment = test_comment
        else:
            suds_comment = suds.null()
        user = User(user_id=executed_by)
        if defect_work_item_id:
            defect = _WorkItem(work_item_id=defect_work_item_id,
                               project_id=self.project_id,
                               fields=["work_item_id"])
            defect_uri = defect.uri
        else:
            defect_uri = None
        self.session.test_management_client.service.addTestRecord(
            self.uri, tc.uri, test_result, suds_comment,
            user.uri, executed, duration, defect_uri)
        self._status_change()

    @tx_wrapper
    def add_test_record_by_object(self, test_record):
        """method add_test_record_by_object, adds a test record for the given
        test case based on the TestRecord object passed in

        Args:
            test_record (TestRecord or Polarion TestRecord):

        Returns:
            None

        References:
            test_management.addTestRecordToTestRun
        """
        self._verify_obj()
        self._check_test_record_exists(test_record.test_case_id)
        if isinstance(test_record, TestRecord):
            suds_object = test_record._suds_object
        elif isinstance(test_record, TestRecord().
                        _suds_object.__class__):
            suds_object = test_record
        self.session.test_management_client.service.addTestRecordToTestRun(
            self.uri, suds_object)
        self._status_change()

    def create_summary_defect(self, defect_template_id=None):
        """method create_summary_defect, adds a new summary _WorkItem for the
        test case based on the _WorkItem template id passed in. If not template
        is passed in, it creates it based on the default template.

        Args:
            defect_template_id (str): the _WorkItem template id to base the
            new summary defect. can be null. default: None

        Returns:
            the created _WorkItem

        References:
            test_management.createSummaryDefect
        """

        self._verify_obj()
        defect_template_uri = None
        if defect_template_id:
            suds_defect_template = _WorkItem(work_item_id=defect_template_id,
                                             project_id=self.project_id)
            defect_template_uri = suds_defect_template._uri
        wi_uri = self.session.test_management_client.service. \
            createSummaryDefect(self.uri, defect_template_uri)
        return _WorkItem(uri=wi_uri)

    def delete_attachment_from_test_record(self, test_case_id, filename):
        """Deletes Test Record Attachment of specified record and
        attachment's file name.

        Args:
            test_case_id: The test case to delete the attachment from
            filename: name of the file to delete

        Returns:
            None

        References:
            test_management.deleteAttachmentFromTestRecord
        """
        record_index = self._get_index_of_test_record(test_case_id)
        self._verify_record_count(record_index)
        self.session.test_management_client.service. \
            deleteAttachmentFromTestRecord(self.uri, record_index, filename)

    def delete_attachment_from_test_step(self, test_case_id, test_step_index,
                                         filename):
        """Deletes Test Step Attachment of the specified step in the specified
        test record.

        Args:
            test_case_id: The test case to delete the attachment from
            filename: name of the file to delete

        Returns:
            None

        References:
            test_management.deleteAttachmentFromTestRecord
        """
        record_index = self._get_index_of_test_record(test_case_id)
        self._verify_test_step_count(record_index, test_step_index)
        self.session.test_management_client.service. \
            deleteAttachmentFromTestStep(self.uri, record_index,
                                         test_step_index, filename)

    def delete_attachment(self, filename):
        """Deletes Test Run Attachment specified by attachment's
        file name. Method is applicable also on Test Run Template.

        Args:
            filename: filename to delete

        Returns:
            None

        References:
            test_management.deleteTestRunAttachment
        """
        self._verify_obj()
        self.session.test_management_client.service. \
            deleteTestRunAttachment(self.uri, filename)

    def get_attachment(self, filename):
        """Gets Test Run Attachment specified by attachment's
        file name. Method is applicable also on Test Run Template.

        Args:
            filename: filename to delete

        Returns:
            TestRunAttachment object

        References:
            test_management.getTestRunAttachment
        """
        self._verify_obj()
        suds_attach = self.session.test_management_client.service. \
            getTestRunAttachment(self.uri, filename)
        return TestRunAttachment(suds_object=suds_attach)

    def get_attachments(self):
        """method get_attachments returns all the attachments for the TestRun

        Args:
            None

        Returns:
            ArrayOfTestRunAttachments object

        References:
            test_management.getTestRunAttachments
        """
        self._verify_obj()
        lst_suds_attach = self.session.test_management_client.service. \
            getTestRunAttachments(self.uri)
        lst_attach = [TestRunAttachment(suds_object=suds_attach)
                      for suds_attach in lst_suds_attach]
        return lst_attach

    def get_custom_field(self, field_name):
        """gets custom field values.

        Args:
            field_name: name of the custom field

        Returns:
            value of the custom field.

        Note: Polarion WSDL currently does not publish the list of custom
              fields, so this function cannot do any verification if the field
              is valid.
        """
        self._verify_obj()
        cf = self._custom_fields
        match = filter(lambda x: x.key == field_name, cf)
        if match:
            return match[0].value
        else:
            return Custom(field_name, None)

    def get_wiki_content(self):
        """method get_wiki_content returns the wiki content for the Test Run

        Args:
            None

        Returns:
            Text object containing the wiki content

        References:
            test_management.getWikiContentForTestRun
        """
        self._verify_obj()
        suds_wiki = self.session.test_management_client.service. \
            getWikiContentForTestRun(self.uri)
        return Text(suds_object=suds_wiki)

    def _set_custom_field(self, field_name, value):
        """sets custom field values.

        Args:
            field_name: name of the custom field

        Returns:
            value of the custom field.

        Note: Polarion WSDL currently does not publish the list of custom
              fields, so this function cannot do any verification if the field
              or value is valid.
        """
        self._verify_obj()
        cf = self._custom_fields
        cust = Custom()
        cust.key = field_name
        cust.value = value
        if cf:
            # check if the custom field already exists and if so, modify it.
            match = filter(lambda x: x.key == field_name, cf)
            if match:
                match[0].value = value
            else:
                cf.append(cust)
        else:
            cf = [cust]
        self._custom_fields = cf

    def update(self):
        """method update updates the testRun object with the attribute values
        currently in the object.

        Args:
            None

        Returns
            None

        References:
            test_management.updateTestRun
        """
        self._verify_obj()
        for field in self._changed_fields:
            self._set_custom_field(field, self._changed_fields[field])
        self._changed_fields = {}
        self.session.test_management_client.service.updateTestRun(
            self._suds_object)

    def update_attachment(self, path, original_filename, title):
        """method update_attachment updates the specified attachment to the
        current test run

        Args:
            path: file path to upload
            original_filename: The file that we want to overwrite with the new
                               file
            title: u.User friendly name of the file

        Returns:
            None

        Notes:
            Raises an error if the test run object is not populated.

        References:
            test_management.updateTestRunAttachment
        """
        self._verify_obj()
        data = self._get_file_data(path)
        filename = os.path.basename(original_filename)
        self.session.test_management_client.service. \
            updateTestRunAttachment(self.uri, filename, title, data)

    def update_summary_defect(self, source, total_failures, total_errors,
                              total_tests, defect_template_id):
        """method update-summary_defect creates or updates the summary defect
        Work Item of a test run.

        Args:
            source (string): source of the summary defect, used to generate
                              the description content.
            total_failures (int): amount of total failures in the test run,
                                  used to generate the description content.
            total_errors (int): amount of total errors in the test run,
                                used to generate the description content.
            total_tests (int): amount of total tests in the test run,
                               used to generate the description content.
            defect_template_id: ID of the defect template Work Item to be
                                used, the configured template will be used if
                                None.

        Returns:
            the created or updated _WorkItem

        References:
            test_management.updateSummaryDefect
        """
        self._verify_obj()
        suds_defect_template = _WorkItem(work_item_id=defect_template_id,
                                         project_id=self.project_id)
        defect_template_uri = suds_defect_template._uri
        wi_uri = self.session.test_management_client.service. \
            updateSummaryDefect(self.uri, source, total_failures, total_errors,
                                total_tests, defect_template_uri)
        return _WorkItem(uri=wi_uri)

    @tx_wrapper
    def update_test_record_by_fields(self, test_case_id,
                                     test_result,
                                     test_comment,
                                     executed_by,
                                     executed,
                                     duration,
                                     defect_work_item_id=None):
        """method update_test_record_by_fields updates a test record.

        Args:
            test_case_id: id of the test case to update.
            test_result: Must be one of the following values:
                                   passed
                                   failed
                                   blocked
            test_comment: (str or Text object) - may be None
            executed_by (str): user id
            executed: date when the test case has been executed
            duration: duration of the test case execution, any negative value
                      is treated as None.
            defect_work_item_id: _WorkItem id of defect, can be None
                                Default: None

        Returns:
            None

        Notes:
            Only a test case that has already been executed may be updated
            using this function. To execute a test record use the
            add_test_record_by_fields function

        References:
            test_management.updateTestRecord
        """
        self._verify_obj()
        testrec = TestRecord(self.project_id, test_case_id)
        testrec.result = test_result
        testrec.comment = test_comment
        testrec.executed_by = executed_by
        testrec.executed = executed
        testrec.duration = duration
        if defect_work_item_id:
            testrec.defect_case_id = defect_work_item_id
        self.update_test_record_by_object(test_case_id, testrec)

    @tx_wrapper
    def update_test_record_by_object(self, test_case_id, test_record):
        """method update_test_record_by_object, adds a test record for the
        given test case based on the TestRecord object passed in

        Args:
            test_case_id (str): the test case id that the record is related to.
            test_record (TestRecord or Polarion TestRecord)

        Returns:
            None

        References:
            test_management.updateTestRecordAtIndex
        """
        self._verify_obj()
        # this function cannot use the _get_index_of_test_record function
        # because this function (specifically and not documented) uses the
        # actual index of the test records and not the index of all
        # executed records.
        test_case_ids = [rec.test_case_id for rec in self._records]
        if test_case_id not in test_case_ids:
            self.add_test_record_by_object(test_record)
        else:
            index = test_case_ids.index(test_case_id)
            if isinstance(test_record, TestRecord):
                suds_object = test_record._suds_object
            elif isinstance(test_record, TestRecord().
                            _suds_object.__class__):
                suds_object = test_record
            self.session.test_management_client.service. \
                updateTestRecordAtIndex(self.uri, index, suds_object)
            self._status_change()

    def update_wiki_content(self, content):
        """method update_wiki_content updates the wiki for the current TestRun

        Args:
            Content (str or Text object)

        Returns:
            None

        References:
            test_management.updateWikiContentForTestRun
        """
        self._verify_obj()
        if content:
            if isinstance(content, basestring):
                obj_content = Text(content=content)
                suds_content = obj_content._suds_object
            elif isinstance(content, Text):
                suds_content = content._suds_object
            else:  # is a suds object
                suds_content = content
        else:
            suds_content = suds.null()
        self.session.test_management_client.service. \
            updateWikiContentForTestRun(self.uri, suds_content)
