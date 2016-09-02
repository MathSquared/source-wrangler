import unittest

from sourcewrangler import retriever

class TestRegisterRetriever(unittest.TestCase):
    
    def test_has_no_run(self):
        def should_break():
            @retriever.register_retriever("test_has_no_run")
            class TestHasNoRunRetriever(object):
                pass

        self.assertRaises(retriever.UnrunnableRetrieverError, should_break)

    def test_duplicate_field(self):
        def should_break():
            @retriever.register_retriever("test_duplicate_field")
            class TestDuplicateFieldRetriever(object):
                def _run(self, retrieval, tmp_folder):
                    pass

                @retriever.required_field("foo")
                def validate_foo(value):
                    return True

                @retriever.optional_field("foo")
                def validate_fooo(value):
                    return True

        self.assertRaises(retriever.DuplicateFieldError, should_break)

    def test_basic(self):
        @retriever.register_retriever("test_basic")
        class TestBasicRetriever(object):
            def _run(self, retrieval, tmp_folder):
                return "pretend this is a temp file", "text/plain"

        self.assertEqual(TestBasicRetriever.protocol, "test_basic")
        self.assertEqual(TestBasicRetriever.required, {})
        self.assertEqual(TestBasicRetriever.optional, {})

        self.assertTrue(TestBasicRetriever.validate({}))
        self.assertFalse(TestBasicRetriever.validate({
            "spurious_field": "lolol"
        }))

        self.assertEqual(TestBasicRetriever().run({}, None), ("pretend this is a temp file", "text/plain"))
        self.assertRaises(retriever.InvalidRetrievalOptionsError, TestBasicRetriever().run, {
            "spurious_field": "lolol"
        }, None)

        self.assertEqual(retriever.get_retriever("test_basic"), TestBasicRetriever)

    def test_required(self):
        @retriever.register_retriever("test_required")
        class TestRequiredRetriever(object):
            def _run(self, retrieval, tmp_folder):
                return "pretend this is a temp file", "text/plain"

            @retriever.required_field("must_be_int")
            def validate_must_be_int(value):
                return type(value) == int

        self.assertEqual(TestRequiredRetriever.protocol, "test_required")
        self.assertEqual(list(TestRequiredRetriever.required), ["must_be_int"])
        self.assertEqual(TestRequiredRetriever.optional, {})

        self.assertFalse(TestRequiredRetriever.validate({}))
        self.assertFalse(TestRequiredRetriever.validate({
            "must_be_int": "no, screw you"
        }))
        self.assertTrue(TestRequiredRetriever.validate({
            "must_be_int": 42
        }))
        self.assertFalse(TestRequiredRetriever.validate({
            "must_be_int": 42,
            "spurious_field": "hehe"
        }))
    
    def test_optional(self):
        @retriever.register_retriever("test_optional")
        class TestOptionalRetriever(object):
            def _run(self, retrieval, tmp_folder):
                return "pretend this is a temp file", "text/plain"

            @retriever.optional_field("may_supply_int")
            def validate_may_supply_int(value):
                return type(value) == int

        self.assertEqual(TestOptionalRetriever.protocol, "test_optional")
        self.assertEqual(TestOptionalRetriever.required, {})
        self.assertEqual(list(TestOptionalRetriever.optional), ["may_supply_int"])

        self.assertTrue(TestOptionalRetriever.validate({}))
        self.assertFalse(TestOptionalRetriever.validate({
            "may_supply_int": "Robert; DROP TABLE Students;--"
        }))
        self.assertTrue(TestOptionalRetriever.validate({
            "may_supply_int": 47
        }))
        self.assertFalse(TestOptionalRetriever.validate({
            "may_supply_int": 47,
            "spurious_field": "haha"
        }))
