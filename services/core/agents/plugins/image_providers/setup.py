from setuptools import setup, find_packages
import json
import os

# Read version from manifest
with open('manifest.json', 'r') as f:
    manifest = json.load(f)

# Read the long description from README.md if it exists
long_description = """
Midjourney image generation provider plugin for Posey

This plugin integrates Midjourney's image generation capabilities into Posey's
image generation system, allowing users to create images using Midjourney's
advanced AI image models.
"""

if os.path.exists('README.md'):
    with open('README.md', 'r') as f:
        long_description = f.read()

setup(
    name=manifest['name'],
    version=manifest['version'],
    description=manifest['description'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=manifest['author'],
    author_email='example@example.com',
    url=manifest.get('website', ''),
    license=manifest.get('license', 'MIT'),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'aiohttp>=3.8.0',
        'asyncio>=3.4.3',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords=' '.join(manifest.get('tags', [])),
    python_requires='>=3.8',
    entry_points={
        'posey.plugins': [
            'midjourney_provider = image_providers'
        ]
    },
) 
