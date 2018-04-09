from setuptools import setup, find_packages
setup(
    name="phonybone_utils",
    version="0.1",
    packages=find_packages(),
    # scripts=['say_hello.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=['mysql_connector', 'ConfigParser', 'sqlalchemy'],

    # package_data={
    #     # If any package contains *.txt or *.rst files, include them:
    #     '': ['*.txt', '*.rst'],
    #     # And include any *.msg files found in the 'hello' package, too:
    #     'hello': ['*.msg'],
    # },

    # metadata for upload to PyPI
    author="Victor Cassen",
    author_email="vmc.swdev@gmail.com",
    description="A variety of general utilities",
    license="MIT",
    keywords="",
    url="http://github.com/phonybone/phonybone_utils/",   # project home page, if any
    # project_urls={
    #     "Bug Tracker": "https://bugs.example.com/HelloWorld/",
    #     "Documentation": "https://docs.example.com/HelloWorld/",
    #     "Source Code": "https://code.example.com/HelloWorld/",
    # }

    # could also include long_description, download_url, classifiers, etc.
)
