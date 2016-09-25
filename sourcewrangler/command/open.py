import command
import webbrowser

@command.register_command("open")
class OpenCommand(object):

    _help = "View a source file."

    _description = "Opens the source file for a given ID, either as stored locally or over the Internet."

    @staticmethod
    def specify_args(parser):
        parser.add_argument("key", type=int,
                            help="The ID of the source to open.")

        fields = parser.add_mutually_exclusive_group(required=True)
        fields.add_argument("-l", action="store_const", dest="medium",
                            const="local",
                            help="Open the version of the file stored on disk.")
        fields.add_argument("-w", action="store_const", dest="medium",
                            const="web",
                            help="Open the file in your web browser.")

        def run(self, sf, args):
            # Sanity check
            if args.key not in sf:
                raise command.UserError("Source ID not found")

            if args.medium == "local":
                fname = sf[args.key]

                # TODO write a better cross-platform openfile thingie; this is a dirty hack
                webbrowser.open(fname)
            elif args.medium == "web":
                url = None
                with sf.open_manifest() as mf:
                    try:
                        url = mf[args.key]["human"]
                    except KeyError:
                        raise command.UserError("No URL defined for this source")
                webbrowser.open(url)
            else:
                assert False
