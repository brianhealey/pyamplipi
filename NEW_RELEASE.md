# Making a new pyamplipi release

```bash
# build the latest
python -m build

# upload to pypi test (go to the pypi test website and make sure everything looks right)
twine upload -r testpypi dist/pyamplipi-${VERSION}*

# upload to pypi
twine upload dist/pyamplipi-${VERSION}*

```
