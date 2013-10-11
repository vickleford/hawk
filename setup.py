from setuptools import setup, find_packages


setup(name='Hawk',
      version='0.1',
      description='Easy setup tool for Rackspace Cloud Monitoring',
      author='Vic Watkins',
      author_email='vic.watkins@rackspace.com',
      url='https://github.com/vickleford/hawk',
      install_requires=['keyring', 'rackspace_monitoring', 'argparse', 'PyYAML'],
      packages=find_packages(),
      entry_points = { 'console_scripts': [
        'hawk = hawk.scripts:spawn'
      ] }
     )