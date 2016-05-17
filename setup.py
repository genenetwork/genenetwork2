# Run setup from python - this script is used by the GNU Guix builder.

from setuptools import setup, find_packages

setup(name='genenetwork2',
      version='2.0',
      author = "The GeneNetwork Team",
      author_email='rwilliams@uthsc.edu',
      url = "https://github.com/genenetwork/genenetwork2/blob/master/README.md",
      description = 'Website and tools for genetics.',
      include_package_data=True,
      packages=['wqflask','etc'],
      scripts=['bin/genenetwork2'],
      # package_data = {
      #   'etc': ['*.py']
      # }
)
