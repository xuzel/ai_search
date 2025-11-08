# Documentation

This directory contains the Sphinx documentation for the AI Search Engine.

## Building Documentation

### Prerequisites

Install Sphinx and dependencies:

```bash
pip install -r ../requirements.txt
```

### Build HTML Documentation

```bash
# From docs/ directory
make html

# View documentation
open build/html/index.html
```

### Build Other Formats

```bash
# PDF (requires LaTeX)
make latexpdf

# ePub
make epub

# Plain text
make text
```

### Clean Build

```bash
make clean
make html
```

## Documentation Structure

```
docs/
├── source/
│   ├── api/                  # API Reference
│   │   ├── routing.rst
│   │   ├── agents.rst
│   │   ├── tools.rst
│   │   ├── llm.rst
│   │   ├── workflow.rst
│   │   ├── web.rst
│   │   └── utils.rst
│   ├── guide/                # User Guide
│   │   ├── installation.rst
│   │   ├── configuration.rst
│   │   ├── usage.rst
│   │   └── deployment.rst
│   ├── dev/                  # Development Guide
│   │   ├── architecture.rst
│   │   ├── testing.rst
│   │   └── contributing.rst
│   ├── conf.py               # Sphinx configuration
│   ├── index.rst             # Main index
│   ├── _static/              # Static files (CSS, images)
│   └── _templates/           # Custom templates
├── build/                    # Generated documentation
│   └── html/                 # HTML output
├── Makefile                  # Build commands
└── README.md                 # This file
```

## Writing Documentation

### reStructuredText Syntax

Sphinx uses reStructuredText (.rst) format:

```rst
Section Title
=============

Subsection
----------

**Bold text**
*Italic text*
``Code text``

.. code-block:: python

   # Python code example
   def example():
       pass

.. note::
   This is a note box

.. warning::
   This is a warning box
```

### Adding New Pages

1. Create `.rst` file in appropriate directory
2. Add to `toctree` in `index.rst` or parent file
3. Rebuild documentation

### Autodoc

API documentation is auto-generated from docstrings:

```rst
.. automodule:: src.routing.base
   :members:
   :undoc-members:
   :show-inheritance:
```

## Deployment

Documentation can be deployed to:

* **Read the Docs**: Automatic builds from GitHub
* **GitHub Pages**: Static hosting
* **S3/CloudFront**: AWS hosting

### Read the Docs

1. Connect GitHub repository
2. RTD auto-builds on push
3. Access at `https://ai-search.readthedocs.io`

### GitHub Pages

```bash
# Build docs
make html

# Copy to gh-pages branch
git checkout gh-pages
cp -r build/html/* .
git add .
git commit -m "Update docs"
git push origin gh-pages
```

## Contributing

When contributing code, update documentation:

1. Add docstrings to new code
2. Update API reference if needed
3. Add usage examples
4. Update user guide for new features

See `dev/contributing.rst` for full guidelines.
