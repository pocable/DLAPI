from setuptools import setup

setup(
    name='DLAPI',
    packages=['dlapi'],
    include_package_data=True,
    install_requires=[
        'flask',
        'myjdapi',
        'requests',
        'Flask-APScheduler',
        'flask-cors',
        'Flask-Limiter',
    ],
)