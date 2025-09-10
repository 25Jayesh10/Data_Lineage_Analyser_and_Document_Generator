# Tool3: Automated SQL Stored Procedure Documentation Generator

## Overview

Tool3 is designed to automate the generation of comprehensive Markdown documentation for SQL stored procedures. It analyzes SQL files and corresponding index JSON files, extracts relevant details, and uses Large Language Models (LLMs) to generate business logic descriptions for each procedure. The output is a well-structured Markdown file suitable for technical and non-technical audiences.

## Features

- Parses SQL files to extract stored procedures, parameters, tables, and called procedures.
- Reads index JSON files for metadata.
- Generates Markdown documentation with:
	- Summary and Table of Contents
	- Detailed procedure documentation (parameters, tables, calls, call graph)
	- Business logic descriptions using LLMs (Gemini, Azure OpenAI, Anthropic, OpenAI, OpenRouter)
- Interactive selection of LLM provider.
- Output includes Mermaid diagrams for call graphs.
## UI: Lineage Chatbot

Tool3 can be used with the Streamlit-based UI (`streamlit_app/app.py`) to interactively query and explore the generated lineage and documentation. The chatbot interface allows users to ask questions about the lineage, understand business logic, and see the impact of changes in a conversational format. It supports multiple LLM providers and model selection for flexible, context-aware answers.

### How the UI is Helpful
- Enables interactive exploration of lineage and documentation.
- Makes technical details accessible to non-technical users.
- Provides instant feedback and explanations using LLMs.
- Supports provider/model selection for tailored responses.

## Packages Used and Their Function

- `google-generativeai`: Connects to Gemini LLM for business logic generation.
- `openai`: Connects to OpenAI and Azure OpenAI for LLM-based descriptions.
- `anthropic`: Connects to Anthropic Claude for LLM-based descriptions.
- `python-dotenv`: Loads environment variables for API keys and configuration.
- `json`, `os`, `re`, `collections`: Standard Python libraries for file handling, parsing, and data manipulation.
- `streamlit`: Powers the interactive UI for querying lineage and documentation.

## Setup Instructions

### 1. Clone the Repository

```cmd
git clone <your-repo-url>
cd Data_Lineage_Analyser_and_Document_Generator\Tool3
```


### 2. Install Python

Tool3 requires Python 3.8 or newer. If you do not have the required version, download and install it from the official Python website:

https://www.python.org/downloads/

After installation, verify your Python version:

```cmd
python --version
```

### 3. Install Required Packages

Install dependencies listed in `requirements.txt`:

```cmd
pip install -r requirements.txt
```

#### Required Packages

- `google-generativeai` (for Gemini)
- `openai` (for OpenAI and Azure OpenAI)
- `anthropic` (for Anthropic Claude)
- `python-dotenv` (for environment variable management)

### 4. Environment Variables

Create a `.env` file in the `Tool3` directory with your API keys:

```
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=your_azure_deployment_name
ANTHROPIC_API_KEY=your_anthropic_api_key
OPEN_ROUTER=your_openrouter_api_key
```

Only the keys for the LLM provider you intend to use are required. If you desire to use any other LLM provider add the respective api key in the `.env` file and add that LLM provider as an option in the `llm_service.py` file and `docgenerator.py` file

## Usage Instructions

### 1. Prepare Input Files

- Place your SQL files in `input/test/` (e.g., `test.sql`).
- Place your index JSON files in `input/index/` (e.g., `index.json`).

### 2. Run the Tool

From the `Tool3` directory, execute:

```cmd
python run_tool3.py
```

#### What Happens

- You will be prompted to select an LLM provider (Gemini, Azure, Anthropic, OpenAI, OpenRouter).
- The tool reads the specified index and SQL files.
- It generates Markdown documentation in `output/documents/procedures.md`.

### 3. Output

- The generated documentation will be found at:  
	`output/documents/procedures.md`
- The console will display status messages and any errors encountered.

## How Tool3 Works

### Main Components

- **run_tool3.py**: Entry point. Handles file paths, prompts for LLM provider, and calls the documentation generator.
- **doc_generator.py**: Core logic for parsing SQL, extracting procedure details, generating Markdown, and integrating LLM-generated business logic.
- **llm_service.py**: Handles connections to various LLM providers and dispatches prompts for business logic descriptions.
- **logging_styles.py**: Provides colored console output for better readability.

### Workflow

1. **File Parsing**: SQL and index files are read and parsed to extract procedures, parameters, tables, and calls.
2. **Markdown Generation**: For each procedure, a Markdown block is created with all relevant details.
3. **Business Logic Description**: The SQL code and metadata are sent to the selected LLM provider, which returns a plain-text business logic description.
4. **Output**: All documentation is compiled and written to a Markdown file.

### Supported LLM Providers

- Gemini (Google)
- Azure OpenAI
- Anthropic Claude
- OpenAI
- OpenRouter

You can select the provider interactively when running the tool. You can also add other LLM provider as per your requirement. 

## Troubleshooting

- Ensure all required API keys are present in your `.env` file.
- If you encounter missing package errors, re-run `pip install -r requirements.txt`.
- For provider-specific errors, check your API key and endpoint configuration.

## Extending Tool3

- To support additional SQL files or indexes, add them to the respective input folders and update the file paths in `run_tool3.py`.
- To add new LLM providers, extend `llm_service.py` with the appropriate client initialization and prompt dispatch logic.


---

If you need further customization or encounter any issues, please refer to the source code or contact the repository maintainer.
