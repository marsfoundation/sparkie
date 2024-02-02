# sparkie
Sparkie is a collection of tools to help users and developers experience Spark

## Installation Instructions
Prerequisite:
- python 3.11
- [poetry](https://python-poetry.org/) (python packaging and dependency management)
    - you can alternatevily use pip and venv
- this repo does not have a .gitignore file, we recommend using a global .gitignore file

1. clone repo locally
```sh 
git clone https://github.com/marsfoundation/sparkie.git
cd sparkie
```

2. activate virtual environment and install dependencies
```sh
poetry shell
```

3. run streamlit
```sh
streamlit run 0_⚡️_Welcome_to_Sparkie.py
```