"""
Main entry point for the budget application.
"""
import argparse
import os
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from budget.parser import TransactionParser
from budget.categorize import Categorizer
from budget.visualizer import BudgetVisualizer
from budget.ai_tools import AITools
from budget.logger import logger
from configs.config import *


def main():
    """Main function to run the budget application from the command line."""
    parser = argparse.ArgumentParser(description='Budget Application')
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import transactions')
    import_parser.add_argument('file', help='Path to transaction file')
    import_parser.add_argument('--source', help='Name of the source (e.g., "Chase Credit Card")')
    
    # Categorize command
    categorize_parser = subparsers.add_parser('categorize', help='Categorize transactions')
    categorize_parser.add_argument('--file', help='Path to transaction file (if not using imported data)')
    categorize_parser.add_argument('--output', help='Path to save categorized transactions')
    categorize_parser.add_argument('--train', action='store_true', help='Train the ML model on categorized data')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze transactions')
    analyze_parser.add_argument('--file', help='Path to categorized transaction file')
    analyze_parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    analyze_parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    analyze_parser.add_argument('--output', help='Directory to save analysis results')
    
    # Visualize command
    visualize_parser = subparsers.add_parser('visualize', help='Create visualizations')
    visualize_parser.add_argument('--file', help='Path to categorized transaction file')
    visualize_parser.add_argument('--type', choices=['spending', 'income', 'trend', 'all'], default='all',
                                help='Type of visualization to create')
    visualize_parser.add_argument('--output', help='Directory to save visualization files')
    
    # AI Assistant command
    assistant_parser = subparsers.add_parser('assistant', help='Get help from AI financial assistant')
    assistant_parser.add_argument('query', nargs='+', help='Query for the AI assistant')
    assistant_parser.add_argument('--provider', choices=['claude', 'openai', 'local'], 
                                help='AI provider to use')
    
    # AI Config command
    ai_config_parser = subparsers.add_parser('ai-config', help='Configure AI settings')
    ai_config_parser.add_argument('--provider', choices=['none', 'claude', 'openai', 'local'], 
                                help='Set AI provider')
    ai_config_parser.add_argument('--status', action='store_true', help='Show AI configuration status')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'import':
        import_transactions(args)
    elif args.command == 'categorize':
        categorize_transactions(args)
    elif args.command == 'analyze':
        analyze_transactions(args)
    elif args.command == 'visualize':
        visualize_transactions(args)
    elif args.command == 'assistant':
        ai_assistant(args)
    elif args.command == 'ai-config':
        configure_ai(args)
    else:
        parser.print_help()

def import_transactions(args):
    """Import transactions from a file."""
    file_path = args.file
    source = args.source
    
    parser = TransactionParser()
    
    if parser.import_file(file_path, source):
        output_path = os.path.join(DATA_DIR, 'imported_transactions.csv')
        parser.export_transactions(output_path)
        
        summary = parser.summary()
        print(f"Successfully imported {summary['count']} transactions")
        print(f"Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"Total income: ${summary.get('total_income', 0):.2f}")
        print(f"Total expenses: ${abs(summary.get('total_expenses', 0)):.2f}")
        print(f"Net: ${summary.get('net', 0):.2f}")
        print(f"Transactions saved to: {output_path}")
    else:
        print(f"Failed to import transactions from {file_path}")

def categorize_transactions(args):
    """Categorize transactions."""
    # Load transactions
    if args.file:
        file_path = args.file
    else:
        file_path = os.path.join(DATA_DIR, 'imported_transactions.csv')
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        transactions = pd.read_csv(file_path)
        print(f"Loaded {len(transactions)} transactions from {file_path}")
    except Exception as e:
        print(f"Error loading transactions: {str(e)}")
        return
    
    # Create categorizer
    categorizer = Categorizer()
    
    # Categorize transactions
    categorized = categorizer.categorize_transactions(transactions)
    
    # Save categorized transactions
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.join(DATA_DIR, 'categorized_transactions.csv')
    
    try:
        categorized.to_csv(output_path, index=False)
        print(f"Saved categorized transactions to {output_path}")
    except Exception as e:
        print(f"Error saving categorized transactions: {str(e)}")
    
    # Show category distribution
    category_counts = categorized['category'].value_counts()
    print("\nCategory distribution:")
    for category, count in category_counts.items():
        print(f"  {category}: {count} transactions")
    
    # Train model if requested
    if args.train:
        print("\nTraining machine learning model...")
        if categorizer.train_model(categorized):
            print("Model trained successfully")
        else:
            print("Failed to train model")

def analyze_transactions(args):
    """Analyze categorized transactions."""
    # Load categorized transactions
    if args.file:
        file_path = args.file
    else:
        file_path = os.path.join(DATA_DIR, 'categorized_transactions.csv')
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        transactions = pd.read_csv(file_path)
        print(f"Loaded {len(transactions)} transactions from {file_path}")
    except Exception as e:
        print(f"Error loading transactions: {str(e)}")
        return
    
    # Convert date column to datetime
    if 'date' in transactions.columns:
        transactions['date'] = pd.to_datetime(transactions['date'])
    
    # Apply date filters
    if args.start:
        start_date = pd.to_datetime(args.start)
        transactions = transactions[transactions['date'] >= start_date]
    
    if args.end:
        end_date = pd.to_datetime(args.end)
        transactions = transactions[transactions['date'] <= end_date]
    
    print(f"Analyzing {len(transactions)} transactions")
    
    # Calculate basic statistics
    total_income = transactions[transactions['amount'] > 0]['amount'].sum()
    total_expenses = transactions[transactions['amount'] < 0]['amount'].sum()
    net = total_income + total_expenses
    
    print(f"\nTotal income: ${total_income:.2f}")
    print(f"Total expenses: ${abs(total_expenses):.2f}")
    print(f"Net: ${net:.2f}")
    
    # Category breakdown
    print("\nExpenses by category:")
    category_expenses = transactions[transactions['amount'] < 0].groupby('category')['amount'].sum().sort_values()
    for category, amount in category_expenses.items():
        percentage = abs(amount) / abs(total_expenses) * 100
        print(f"  {category}: ${abs(amount):.2f} ({percentage:.1f}%)")
    
    # Monthly summary
    if 'date' in transactions.columns:
        print("\nMonthly summary:")
        transactions['month'] = transactions['date'].dt.to_period('M')
        monthly = transactions.groupby('month').agg({'amount': 'sum'})
        for month, row in monthly.iterrows():
            print(f"  {month}: ${row['amount']:.2f}")
    
    # Generate insights using AI if available
    ai_tools = AITools()
    if ai_tools.is_enabled() and AI_API['capabilities']['spending_insights']:
        print("\nGenerating AI insights...")
        
        # Prepare summary data
        summary_data = {
            'total_income': float(total_income),
            'total_expenses': float(abs(total_expenses)),
            'net': float(net),
            'expenses_by_category': {cat: float(abs(amt)) for cat, amt in category_expenses.items()},
            'transaction_count': len(transactions),
            'date_range': {
                'start': transactions['date'].min().strftime('%Y-%m-%d') if 'date' in transactions.columns else None,
                'end': transactions['date'].max().strftime('%Y-%m-%d') if 'date' in transactions.columns else None
            }
        }
        
        insights = ai_tools.generate_insights(summary_data)
        
        if insights and 'insights' in insights:
            print("\nAI Insights:")
            for i, insight in enumerate(insights['insights'], 1):
                print(f"  {i}. {insight['title']}")
                print(f"     {insight['description']}")
                print()
    
    # Save analysis results if requested
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save summary to CSV
        summary_data = {
            'metric': ['Total Income', 'Total Expenses', 'Net'],
            'amount': [total_income, abs(total_expenses), net]
        }
        pd.DataFrame(summary_data).to_csv(output_dir / 'summary.csv', index=False)
        
        # Save category breakdown to CSV
        category_df = pd.DataFrame({
            'category': category_expenses.index,
            'amount': category_expenses.values.round(2).abs(),
            'percentage': (category_expenses.values / total_expenses * 100).round(2).abs()
        })
        category_df.to_csv(output_dir / 'category_breakdown.csv', index=False)
        
        # Save monthly summary to CSV if available
        if 'month' in transactions.columns:
            monthly.reset_index().to_csv(output_dir / 'monthly_summary.csv', index=False)
        
        print(f"Analysis results saved to {output_dir}")

def visualize_transactions(args):
    """Create visualizations for categorized transactions."""
    # This function would require implementing the BudgetVisualizer class
    print("Visualization feature is not implemented yet")

def ai_assistant(args):
    """Interact with the AI financial assistant."""
    query = ' '.join(args.query)
    
    ai_tools = AITools()
    
    # Switch provider if specified
    if args.provider:
        ai_tools.switch_provider(args.provider)
    
    if not ai_tools.is_enabled():
        print("AI assistant is not enabled. Use 'ai-config' command to configure.")
        return
    
    if not AI_API['capabilities']['financial_assistant']:
        print("Financial assistant capability is not enabled in configuration.")
        return
    
    print(f"Query: {query}")
    print("\nThinking...")
    
    response = ai_tools.financial_assistant(query)
    
    print("\nResponse:")
    print(response)

def configure_ai(args):
    """Configure AI settings."""
    ai_tools = AITools()
    
    # Show status if requested
    if args.status:
        provider = AI_API['provider']
        
        print(f"Current AI provider: {provider}")
        
        if provider == 'claude':
            enabled = AI_API['claude']['enabled']
            has_key = bool(AI_API['claude']['api_key'])
            model = AI_API['claude']['model']
            print(f"Claude enabled: {enabled}")
            print(f"API key configured: {has_key}")
            print(f"Model: {model}")
        elif provider == 'openai':
            enabled = AI_API['openai']['enabled']
            has_key = bool(AI_API['openai']['api_key'])
            model = AI_API['openai']['model']
            print(f"OpenAI enabled: {enabled}")
            print(f"API key configured: {has_key}")
            print(f"Model: {model}")
        elif provider == 'local':
            enabled = AI_API['local']['enabled']
            url = AI_API['local']['api_url']
            model = AI_API['local']['model']
            print(f"Local model enabled: {enabled}")
            print(f"API URL: {url}")
            print(f"Model: {model}")
        
        print("\nCapabilities:")
        for capability, enabled in AI_API['capabilities'].items():
            print(f"  {capability}: {enabled}")
        
        return
    
    # Set provider if specified
    if args.provider:
        if ai_tools.switch_provider(args.provider):
            print(f"AI provider switched to {args.provider}")
            
            # Update .env file
            env_path = Path('.env')
            if env_path.exists():
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                with open(env_path, 'w') as f:
                    for line in lines:
                        if line.startswith('AI_PROVIDER='):
                            f.write(f'AI_PROVIDER={args.provider}\n')
                        else:
                            f.write(line)
                
                print(f"Updated .env file with new provider: {args.provider}")
            else:
                print("Warning: .env file not found. Settings will not persist after restart.")
        else:
            print(f"Failed to switch AI provider to {args.provider}")

if __name__ == '__main__':
    main()