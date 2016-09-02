import unittest

from sourcewrangler import command

class TestCommandRetriever(unittest.TestCase):
    
    def test_incomplete(self):
        def should_break():
            @command.register_command("test_incomplete")
            class TestIncompleteCommand(object):
                pass

        self.assertRaises(command.ImproperlyDefinedCommandError, should_break)

    def test_basic(self):
        @command.register_command("test_basic")
        class TestBasicCommand(object):
            @staticmethod
            def specify_args(argparse):
                pass

            def run(self, sf, args):
                pass

        self.assertEqual(TestBasicCommand.name, "test_basic")
        self.assertTrue(command.has_command("test_basic"))
        self.assertEqual(command.get_command("test_basic"), TestBasicCommand)
