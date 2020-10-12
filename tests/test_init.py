"""Test the icon-prometheus-exporter package."""

# import src
#
# def test_version_is_string():
#     assert isinstance(icon-prometheus-exporter.__version__, str)

from icon_network_exporter import Exporter, main


# def test_parser():
#     parser = parse_args(['--exporter_port', '6100'])
#     assert parser.exporter_port == 6100

def test_main():
    # parser = parse_args(['--exporter_port', '6100'])
    e = Exporter()
    e.serve_forever()
    # main()
