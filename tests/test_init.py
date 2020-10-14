"""Test the icon-prometheus-exporter package."""

# import src
#
# def test_version_is_string():
#     assert isinstance(icon-prometheus-exporter.__version__, str)

from icon_network_exporter import main


def test_main():
    main()
