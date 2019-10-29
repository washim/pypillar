from setuptools import setup
from pypillar import __version__

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pypillar',
    version=__version__,
    packages=['pypillar'],
    license='MIT license',
    description='Distribute large python execution in task',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Washim Ahmed',
    author_email='washim.ahmed@gmail.com',
    python_requires='>=3',
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-WTF',
        'WTForms'
    ],
    entry_points={
        'console_scripts': [
            'pypillar=pypillar:cli'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ]
)
