from setuptools import setup

setup(
    name='ilse',
    version='0.6.0',
    py_modules=['ilse'],
    install_requires=[
        'click',
        'requests',
    ],
    entry_points='''
        [console_scripts]
        ilse=ilse:cli
    ''',
)
