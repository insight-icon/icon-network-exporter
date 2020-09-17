from setuptools import setup, find_packages

url = ""
version = "0.1.0"
readme = open('README.md').read()

setup(
    name="icon-network-exporter",
    packages=["icon_network_exporter"],
    version=version,
    description="exporter agent for icon blockchain",
    long_description=readme,
    entry_points={
        'console_scripts': [
            'icon-network-exporter=icon_network_exporter:main',
        ],
    },
    install_requires=[
        'requests>=2,<3',
        'prometheus_client'
    ],
    include_package_data=True,
    author="Haitham Ghalwash",
    author_email="h.ghalwash@gmail.com",
    url=url,
    download_url="{}/tarball/{}".format(url, version),
    license="MIT"
)
