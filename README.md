# AI-Powered Budget App

A Python-based personal finance application that uses AI to categorize transactions, provide financial insights, and help manage your budget.

## Features

- **Transaction Import**: Import transactions from bank and credit card statements in various formats (CSV, Excel, OFX/QFX)
- **Smart Categorization**: Automatically categorize transactions using rule-based and AI approaches
- **Financial Analysis**: Generate spending reports and budget recommendations
- **Data Visualization**: Create charts and graphs to visualize your financial data
- **AI Integration**: Connect to Claude or ChatGPT APIs for enhanced financial insights
- **Financial Assistant**: Ask questions about your finances and get AI-powered answers

## Project Structure

```
budget/
├── __init__.py
├── __main__.py
├── categorize.py      # Transaction categorization module
├── config.py          # Application configuration
├── logger.py          # Logging utilities
├── main.py            # Command line interface 
├── parser.py          # Transaction import and parsing
├── visualizer.py      # Visualization functions
├── ai_tools.py        # AI integration (Claude/ChatGPT)
├── data/              # Data storage
├── logs/              # Application logs
├── tests/             # Test suite
├── .env               # Environment variables
├── README.md          # Documentation
└── requirements.txt   # Dependencies
```

## Installation

1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Configure your API keys in the `.env` file:
   ```
   CLAUDE_API_KEY=your_claude_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

### Command Line Interface

The app provides a command-line interface for common operations:

```bash
# Import transactions
python -m budget import bank_statement.csv --source "Chase Checking"

# Categorize transactions
python -m budget categorize --train

# Analyze your finances
python -m budget analyze --start 2023-01-01 --end 2023-12-31

# Create visualizations
python -m budget visualize --type spending

# Ask the AI financial assistant
python -m budget assistant "How much did I spend on restaurants last month?"

# Configure AI settings
python -m budget ai-config --provider claude
python -m budget ai-config --status
```

### AI Integration

The app can use multiple AI providers:

- **Claude API**: Anthropic's Claude for high-quality financial analysis
- **OpenAI API**: ChatGPT for transaction categorization and insights
- **Local Models**: Support for local LLMs via tools like Ollama

Configure your preferred AI provider in the `.env` file or using the command line interface.

## Development

### Adding New Features

1. Add your feature to the appropriate module
2. Update the CLI in `main.py` if needed
3. Add tests in the `tests/` directory

### Running Tests

```bash
pytest tests/
```

## License

[MIT License](LICENSE)