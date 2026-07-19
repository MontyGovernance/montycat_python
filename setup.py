from setuptools import setup, find_packages

setup(
    name='montycat',
    version='1.0.5',
    description=(
        'Self-hosted vector database + NoSQL with built-in AI semantic search — the async '
        'Python client for Montycat. A Rust-powered, AI-native Pinecone / Weaviate / Chroma '
        'alternative for RAG, AI agents & LLM memory.'
    ),
    packages=find_packages(),
    zip_safe=False,
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='MontyGovernance',
    author_email='eugene.and.monty@gmail.com',
    url='https://montygovernance.com',
    license='MIT',
    install_requires=['orjson', 'xxhash'],
    project_urls={
        'Homepage': 'https://montygovernance.com',
        'Documentation': 'https://montygovernance.com',
        'Source': 'https://github.com/MontyGovernance/montycat_python',
        'Issues': 'https://github.com/MontyGovernance/montycat_python/issues',
        'Changelog': 'https://github.com/MontyGovernance/montycat_python/releases',
        'Docker Hub': 'https://hub.docker.com/r/montygovernance/montycat',
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: AsyncIO",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=(
        "vector-database vector-search semantic-search embeddings similarity-search knn hnsw "
        "nosql database database-client rag retrieval-augmented-generation ai ai-agents "
        "agent-memory ai-memory llm mcp self-hosted embedded-database "
        "pinecone-alternative weaviate-alternative chroma-alternative qdrant-alternative "
        "redis-alternative data-mesh async asyncio rust realtime key-value cache montycat"
    ),
    python_requires='>=3.9',
)
