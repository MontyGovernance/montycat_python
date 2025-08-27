from setuptools import setup, find_packages

setup(
    name='montycat',
    version='0.1.45',
    description='A Python client for MontyCat, NoSQL store utilizing Data Mesh architecture.',
    packages=find_packages(),
    zip_safe=False,
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='MontyGovernance',
    author_email='eugene.and.monty@gmail.com',
    install_requires=['orjson', 'xxhash'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)