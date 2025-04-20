from setuptools import setup, find_packages

setup(
    name='montycat',
    version='0.1.39',
    description='A Python client for MontyCat, NoSQL store utilizing Data Mesh architecture.',
    packages=find_packages(),
    zip_safe=False,
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='MontyGovernance',
    author_email='eugene.and.monty@gmail.com',
    package_data={
        'montycat.store_functions': ['*.py'],        
        'montycat.core': ['*.py']
    },
    install_requires=['orjson', 'xxhash', 'asyncio'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
