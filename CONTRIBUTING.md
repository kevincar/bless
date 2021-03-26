## Contributing to `bless`

### Bugs & Problems with bless

- Check the issue has not already been reported
- If you're unable to find an issue addressing the problem, [open a new one](https://github.com/kevincar/bless/issues/new?assignees=&labels=&template=bug_report.md&title=). 
  - Be sure to include a **title and clear description** and as much relevant information as possible
  - Preferrably include a snippit of code to use that can reproduce the error if possible

### Suggestting new features

- Open a new [feature request](https://github.com/kevincar/bless/issues/new?assignees=&labels=&template=feature_request.md&title=)

- If you already have code to implement the new feature, open a pull request and mention the associated issue and see the [pull requests section](#pull-requsts) below

### Pull Requests

- If you haven't already, fork this repository
- Where appropriate, and if possible, please ensure that any new files or functions that are added have an associated test to validate it
- All Pull requests must pass tests
  - The tests include both automated test using GitHub Actions for continuous integration as well as hardware tests that cannot be automated.
  - To run the hardware tests you can run the following command from the root of the project and use a Bluetooth interrogating app such as LightBlue to validate that the server and its functions work

**bash**
```bash
TEST_HARDWARE=True python -m pytest -s
```
**powershell**
```powershell
$env:TEST_HARDWARE="True"
python -m pytest -s
```
