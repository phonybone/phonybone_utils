from setuptools import setup, find_packages

from pbutils import version

with open('requirements.txt') as reqs:
    deps = reqs.readlines()


setup(
    name="phonybone_utils",
    version=version,
    packages=find_packages(),
    scripts=['bin/version_bump', 'bin/arequest', 'bin/mkjwt', 'bin/jwt_decode'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=deps,

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
