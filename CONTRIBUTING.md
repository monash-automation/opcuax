# Contribute

## Prepare

### Fork and Clone Repo

```shell
git clone https://github.com/<your-id>/opcuax
cd opcuax
```

### Setup Environment

Create virtual environment

```shell
python -m venv venv
```

Or if you have `virtualenv` installed (`pip install virtualenv`)

```shell
virtualenv venv
```

Activate virtual environment

```shell
# Mac or Linux
source venv/bin/activate

# Windows
venv\Scripts\activate.bat
```

Install dependencies using [Poetry](https://python-poetry.org/docs/)

```shell
pip install poetry
poetry install
```

### Configure Git

```shell
git config --global user.name 'your name'
git config --global user.email 'your email'

pre-commit install
```

## Coding

* create a new branch
* code for a feature or bugfix
* add unit tests under `./tests`
* update docs if needed

Try [opcua-client-gui](https://github.com/FreeOpcUa/opcua-client-gui) if you need an OPC UA client

## Test

### Unit Test

```shell
pytest tests/
```

### Static Checking

```shell
pip install mypy
mypy .
```

Please make sure all tests are passed before you commit

## Submit

* commit and push to your remote repo
* submit a pull request
