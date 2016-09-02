import command

@command.register_command("values")
class ValuesCommand(object):
    
    _help = "Find all values of a given field"

    _description = "Prints all unique values of a given metadata field, whether the author, category, media type, or title of each source."
    
    @staticmethod
    def specify_args(parser):
        fields = parser.add_mutually_exclusive_group()
        fields.add_argument("-a", action="store_const", dest="field",
                            const="author",
                            help="Print all unique authors.")
        fields.add_argument("-c", action="store_const", dest="field",
                            const="category",
                            help="Print all unique categories.")
        fields.add_argument("-m", action="store_const", dest="field",
                            const="media",
                            help="Print all unique media types.")
        fields.add_argument("-t", action="store_const", dest="field",
                            const="title",
                            help="Print all unique titles.")

    def run(self, sf, args):
        print "Found the following values for '%s':" % args.field
        with mf as sf.open_manifest():
            for value in sorted(mf.values(args.field)):
                print value
