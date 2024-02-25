# Python currency conversion
This is wrapper for currancylayer API


## Development
### How to generate requirements.txt
```bash
pipenv requirements > requirements.txt
pipenv requirements --dev > requirements_dev.txt
```
### Hot use pre-commit
use pre-commit to run all checks
```bash
pre-commit run --all-files
```

### How to run tests
```bash
pytest
```
or
```bash
tox -e pytest
```
