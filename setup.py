from setuptools import setup, find_packages

setup(
    name='azubar',
    version='0.0.3.2',
    packages=find_packages(),
    license="MIT",
    install_requires=[],
    author='Kazekawa-azusa',
    description='A progerss bar creator',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Kazekawa-azusa/azubar',
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
)
