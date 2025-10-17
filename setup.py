from setuptools import setup, find_packages

setup(
    name='montycat',
    version='1.0.0',
    description='A Python client for Montycat, NoSQL database utilizing Data Mesh architecture.',
    packages=find_packages(),
    zip_safe=False,
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='MontyGovernance',
    author_email='eugene.and.monty@gmail.com',
    install_requires=['orjson', 'xxhash'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="database nosql sql data-mesh cache key-value realtime montycat",
    python_requires='>=3.9',
)