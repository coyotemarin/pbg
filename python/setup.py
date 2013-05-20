try:
    from setuptools import setup
    setup  # quiet "redefinition of unused ..." warning from pyflakes
    # arguments that distutils doesn't understand
    setuptools_kwargs = {
        'install_requires': [
            'BeautifulSoup4',
            'html5lib',
            'microdata',
            'pyassert',
        ],
        'provides': ['pbg'],
        #'test_suite': 'tests.suite.load_tests',
        #'tests_require': ['unittest2', 'mock'],
    }
except ImportError:
    from distutils.core import setup
    setuptools_kwargs = {}

import pbg

setup(
    author='David Marin',
    author_email='dm@davidmarin.org',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    description='Parse Buying Guides (for great justice!)',
    license='Apache',
    name='pbg',
    packages=['pbg',
              'pbg.cornucopia',
              'pbg.hrc',
              'pbg.hrc.buyersguide'],
    url='http://github.com/davidmarin/pbg',
    version=pbg.__version__,
    **setuptools_kwargs
)
