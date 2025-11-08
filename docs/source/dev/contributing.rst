Contributing Guide
==================

Thank you for your interest in contributing to the AI Search Engine!

Getting Started
---------------

1. Fork the Repository
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Fork on GitHub, then clone
   git clone https://github.com/yourusername/ai_search.git
   cd ai_search

2. Set Up Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Install pre-commit hooks (optional)
   pre-commit install

3. Create a Branch
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create feature branch
   git checkout -b feature/my-feature

   # Or bugfix branch
   git checkout -b fix/issue-123

Development Workflow
--------------------

1. Make Changes
~~~~~~~~~~~~~~~

* Follow code style guidelines
* Add tests for new features
* Update documentation

2. Run Tests
~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Run with coverage
   pytest tests/ --cov=src --cov-report=html

   # Check coverage increased
   open htmlcov/index.html

3. Check Code Quality
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Format code
   black src/ tests/

   # Check linting
   flake8 src/ tests/

   # Type checking
   mypy src/

   # Find dead code
   vulture src/

4. Commit Changes
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Stage changes
   git add .

   # Commit with descriptive message
   git commit -m "Add feature: intelligent query routing"

   # Follow conventional commits format
   # feat: New feature
   # fix: Bug fix
   # docs: Documentation
   # test: Tests
   # refactor: Refactoring
   # chore: Maintenance

5. Push and Create PR
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Push to your fork
   git push origin feature/my-feature

   # Create pull request on GitHub
   # Provide clear description of changes

Code Style Guidelines
---------------------

Python Style
~~~~~~~~~~~~

Follow PEP 8 with these specifics:

* **Line length**: 88 characters (Black default)
* **Indentation**: 4 spaces
* **Quotes**: Double quotes for strings
* **Imports**: Sorted and grouped
* **Type hints**: Use type hints for public APIs

Example:

.. code-block:: python

   from typing import List, Optional

   class MyClass:
       """Class docstring.

       Args:
           param1: Description of param1
           param2: Description of param2
       """

       def __init__(self, param1: str, param2: int = 10):
           self.param1 = param1
           self.param2 = param2

       async def my_method(self, arg: str) -> Optional[List[str]]:
           """Method docstring.

           Args:
               arg: Description of arg

           Returns:
               Description of return value
           """
           # Implementation
           return None

Docstring Format
~~~~~~~~~~~~~~~~

Use Google-style docstrings:

.. code-block:: python

   def function(arg1: str, arg2: int) -> bool:
       """Short description of function.

       Longer description if needed. Can span multiple lines
       and include details about implementation.

       Args:
           arg1: Description of arg1
           arg2: Description of arg2

       Returns:
           Description of return value

       Raises:
           ValueError: Description of when this is raised
           TypeError: Description of when this is raised

       Examples:
           >>> function("test", 10)
           True
       """
       pass

Naming Conventions
~~~~~~~~~~~~~~~~~~

* **Classes**: ``PascalCase``
* **Functions**: ``snake_case``
* **Constants**: ``UPPER_SNAKE_CASE``
* **Private**: ``_leading_underscore``
* **Modules**: ``lowercase``

Testing Guidelines
------------------

Test Coverage
~~~~~~~~~~~~~

* Aim for 80%+ coverage on new code
* All new features must have tests
* Test both success and error cases

Test Organization
~~~~~~~~~~~~~~~~~

.. code-block:: python

   @pytest.mark.unit  # Or integration, api, etc.
   class TestMyFeature:
       """Test suite for MyFeature"""

       @pytest.fixture
       def feature(self):
           """Fixture for feature instance"""
           return MyFeature()

       def test_basic_functionality(self, feature):
           """Test basic functionality"""
           result = feature.do_something()
           assert result is not None

       def test_error_handling(self, feature):
           """Test error handling"""
           with pytest.raises(ValueError):
               feature.do_something(invalid_input)

Documentation
-------------

Update Documentation
~~~~~~~~~~~~~~~~~~~~

When adding features, update:

* Docstrings in code
* API reference (Sphinx autodoc)
* User guide examples
* README if needed

Build Documentation
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build Sphinx docs
   cd docs
   make html

   # View docs
   open build/html/index.html

Adding Examples
~~~~~~~~~~~~~~~

Include practical examples in documentation:

.. code-block:: python

   # Good: Practical example
   """
   Examples:
       >>> router = create_router(config, llm_manager)
       >>> decision = await router.route("What is Python?")
       >>> print(decision.primary_task_type)
       TaskType.RESEARCH
   """

   # Avoid: Abstract example
   """
   Examples:
       >>> result = do_something()
   """

Pull Request Guidelines
-----------------------

PR Title
~~~~~~~~

Use conventional commit format:

* ``feat: Add support for Gemini LLM``
* ``fix: Fix router classification for math queries``
* ``docs: Update installation guide``
* ``test: Add tests for RAG agent``

PR Description
~~~~~~~~~~~~~~

Include:

1. **What**: What changes are included
2. **Why**: Why these changes are needed
3. **How**: How the changes work
4. **Testing**: How the changes were tested

Template:

.. code-block:: markdown

   ## What
   Added support for Gemini LLM provider.

   ## Why
   To provide more LLM options for users.

   ## How
   - Created GeminiClient class inheriting from BaseLLM
   - Added configuration in config.yaml
   - Added initialization in LLMManager

   ## Testing
   - Added unit tests for GeminiClient
   - Tested manually with API key
   - All existing tests pass

   ## Checklist
   - [x] Tests added
   - [x] Documentation updated
   - [x] Code formatted with Black
   - [x] Type hints added
   - [x] All tests pass

Review Process
~~~~~~~~~~~~~~

1. Create PR with clear description
2. Address review comments
3. Keep PR focused (one feature per PR)
4. Rebase if needed to keep history clean

Common Contribution Areas
-------------------------

Adding a New LLM Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create client in ``src/llm/``
2. Inherit from ``BaseLLM``
3. Implement ``complete()`` and ``is_available()``
4. Add configuration in ``config.yaml``
5. Register in ``LLMManager._initialize_providers()``
6. Add tests
7. Update documentation

Adding a New Tool
~~~~~~~~~~~~~~~~~

1. Create tool in ``src/tools/``
2. Implement async interface
3. Add error handling
4. Add configuration if needed
5. Export in ``__init__.py``
6. Add tests
7. Update documentation

Adding a New Router Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create router in ``src/routing/``
2. Inherit from ``BaseRouter``
3. Implement ``route()`` method
4. Add to factory
5. Add tests
6. Update documentation

Improving Tests
~~~~~~~~~~~~~~~

1. Identify low-coverage modules
2. Add unit tests
3. Add integration tests
4. Ensure tests are fast
5. Use appropriate markers

Improving Documentation
~~~~~~~~~~~~~~~~~~~~~~~

1. Fix typos and errors
2. Add missing examples
3. Update outdated info
4. Improve clarity
5. Add diagrams

Code Review Checklist
---------------------

For Reviewers
~~~~~~~~~~~~~

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security issues introduced
- [ ] Performance impact is acceptable
- [ ] Breaking changes are documented
- [ ] Error handling is appropriate

For Contributors
~~~~~~~~~~~~~~~~

Before requesting review:

- [ ] All tests pass locally
- [ ] Code is formatted (Black)
- [ ] Type hints are added
- [ ] Docstrings are complete
- [ ] Documentation is updated
- [ ] Commits are clean and descriptive
- [ ] PR description is clear

Getting Help
------------

* **Documentation**: Read the docs first
* **Issues**: Search existing issues
* **Discussions**: Use GitHub Discussions
* **Questions**: Ask in issues with "question" label

Issue Reporting
---------------

Bug Reports
~~~~~~~~~~~

Include:

1. Description of the bug
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Environment (OS, Python version)
6. Relevant logs/errors

Feature Requests
~~~~~~~~~~~~~~~~

Include:

1. Use case description
2. Proposed solution
3. Alternatives considered
4. Willingness to implement

Community Guidelines
--------------------

* Be respectful and welcoming
* Assume good intentions
* Provide constructive feedback
* Help others learn and grow
* Give credit where due

License
-------

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank You!
----------

Thank you for contributing to the AI Search Engine! Your contributions make this project better for everyone.
