#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README文件作为长描述
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name='mergefile',
    version='1.0.0',
    description='合并多个文件到XML或Markdown格式，适合提供给大模型阅读',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Liu Shengli',
    author_email='liushengli203@163.com',
    url='https://github.com/gseismic/mergefile',
    py_modules=['mergefile'],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Documentation',
        'Topic :: Text Processing',
        'Topic :: Utilities',
    ],
    keywords='merge files xml markdown llm ai documentation',
    entry_points={
        'console_scripts': [
            'mergefile=mergefile:main',
        ],
    },
    install_requires=[
        # 没有外部依赖，只使用Python标准库
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/gseismic/mergefile/issues',
        'Source': 'https://github.com/gseismic/mergefile',
        'Documentation': 'https://github.com/gseismic/mergefile/blob/main/README.md',
    },
)
