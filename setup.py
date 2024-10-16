# setup.py
from setuptools import setup, find_packages

setup(
    name='montycat',
    version='0.1.1',
    description='A Python client for MontyCat, NoSQL store utilizing Data Mesh architecture.',
    packages=find_packages(),
    zip_safe=False,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='MontyGovernance',
    author_email='eugene.and.monty@gmail.com',
    include_package_data=True,
    install_requires=['orjson', 'xxhash', 'asyncio'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
