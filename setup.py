import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="turCy", # Replace with your own username
    version="0.0.14",
    author="Christian Klose",
    author_email="chris.klose@gmx.net",
    description="A package for German Open Informtion Extraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ChrisChross/turCy",
    packages=setuptools.find_packages(),
    keywords="openie turcy information extraction spacy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)