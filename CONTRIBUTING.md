# Contribute

## Prepare

### Fork and Clone Repo

```shell
git clone https://github.com/<your-id>/opcuax
cd opcuax
```

### Setup Environment

Install [Poetry](https://python-poetry.org/docs/)

```shell
poetry shell
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
mypy opcuax
```

Please make sure all tests are passed before you commit

## Submit

* commit and push to your remote repo
* submit a pull request
