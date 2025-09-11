# Tool4: Data Lineage Analysis and Documentation Generator

## Overview

Tool4 automates the analysis and visualization of database lineage from SQL stored procedures, functions, and triggers. It validates input files, generates lineage data, creates Mermaid diagrams for visualizing relationships, and produces Markdown documentation. Tool4 is modular and can be extended for additional lineage analysis or documentation needs.

## Features

- Validates `index.json` and `ast.json` files against their schemas and checks for consistency.
- Analyzes SQL AST and index files to generate a comprehensive lineage JSON file.
- Generates Mermaid diagrams to visualize database object relationships (procedures, tables, functions, triggers, columns).
- Converts Mermaid diagrams to Markdown for easy sharing and documentation.
- Modular scripts for validation, lineage analysis, diagram generation, and conversion.

## Setup Instructions

### 1. Install Python

Tool4 requires Python 3.8 or newer. If you do not have the required version, download and install it from:

https://www.python.org/downloads/

Verify your Python installation:

```cmd
python --version
```

### 2. Install Required Packages

Navigate to the main project directory and install dependencies (if any are listed in `requirements.txt`):

```cmd
pip install -r requirements.txt
```

Tool4 uses standard Python libraries (`os`, `json`, `logging`, `re`, etc.) and may require `jsonschema` for validation. If not present, install it:

```cmd
pip install jsonschema
```

## Usage Instructions

### 1. Prepare Input Files

- Place your index JSON files in `input/index/` (e.g., `index.json`).
- Place your AST JSON files in `input/ast/` (e.g., `ast.json`).

### 2. Run Tool4

From the `Tool4` directory, execute:

```cmd
python run_tool4.py
```

#### What Happens

- The tool validates the input files against their schemas and checks for consistency.
- It analyzes the lineage and generates `output/lineage.json`.
- Mermaid diagrams are created in `output/diagrams/lineage_diagram.mmd`.
- Markdown documentation is generated in `output/diagrams/lineage_diagram.md`.
- The console displays status messages and any errors encountered.

## How Tool4 Works

### Main Components

- **run_tool4.py**: Main entry point. Orchestrates validation, lineage analysis, diagram generation, and Markdown conversion.
- **src/analyze_lineage.py**: Core logic for parsing AST and index files, extracting relationships, and generating lineage data.
- **src/validation_script.py**: Validates input files against schemas and checks for consistency.
- **src/generate_mermaid.py**: Generates Mermaid diagrams from lineage data for visual representation.
- **src/convert_mmd_to_md.py**: Converts Mermaid diagram files to Markdown format.
- **src/lineage_to_index.py**: (Optional) Generates a new index from lineage and Mermaid data.
- **src/logging_styles.py**: Provides colored console output for better readability.

### Workflow

1. **Validation**: Checks that `index.json` and `ast.json` match their schemas and are consistent.
2. **Lineage Analysis**: Parses AST and index files to build a lineage map of procedures, tables, functions, triggers, and columns.
3. **Diagram Generation**: Creates a Mermaid diagram to visualize relationships and data flow.
4. **Markdown Conversion**: Converts the diagram to Markdown for documentation.

## UI: Lineage Chatbot


Tool4 provides two user-friendly chatbot interfaces for interacting with lineage data:

### 1. Command-Line Chatbot (CLI)
- Located in `lineage_chat_bot/main.py` and related files.
- Allows users to query lineage data directly from the terminal.
- Supports multiple LLM providers (OpenAI, Gemini, Azure, OpenRouter) and model selection.
- Useful for quick, scriptable Q&A and for users comfortable with the command line.

### 2. Streamlit Chatbot UI
- Located in `streamlit_app/app.py` and `UI/app.py`.
- Provides a web-based dashboard for interactive exploration of lineage data, diagrams, and documentation.
- Users can select files, view Mermaid diagrams, read business logic documentation, and chat with the assistant about the loaded data.
- Makes lineage data accessible to non-technical users and supports interactive Q&A about database objects and their relationships.
- Supports provider/model selection for flexible, context-aware answers.

Both UIs help users understand data flow, the impact of changes, and provide detailed insights into the lineage. The conversational format makes it easy to explore and clarify complex relationships in your database.

## Packages Used and Their Function

- `jsonschema`: Validates input files against their schemas.
- `os`, `json`, `logging`, `re`: Standard Python libraries for file handling, data parsing, logging, and regex operations.
- `streamlit`: Powers the interactive UI for querying lineage data.
- `dotenv`: Loads environment variables for API keys and configuration.
- LLM SDKs (`openai`, `google-generativeai`, etc.): Used for connecting to and querying LLM providers.


## Troubleshooting

- Ensure all required input files are present in the correct directories.
- If you encounter missing package errors, re-run `pip install -r requirements.txt` or install missing packages individually.
- For schema validation errors, check your input files for correct structure and required fields.

## Extending Tool4

- To support additional input files, add them to the respective input folders and update file paths in `run_tool4.py`.
- To add new analysis or visualization features, extend the relevant scripts in the `src/` directory.


---

For further customization or issues, refer to the source code or contact the repository maintainer.
