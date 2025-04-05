"""
Transaction parser module for importing and processing bank and credit card statements.
"""
import os
import pandas as pd
import numpy as np
import re
from datetime import datetime
import csv
from pathlib import Path

from configs.config import BANK_IMPORT
from .logger import logger

class TransactionParser:
    """
    Parser for bank and credit card transaction data from various file formats.
    """
    
    def __init__(self):
        """Initialize the transaction parser."""
        self.transactions = pd.DataFrame()
        self.source_files = []
        
    def import_file(self, file_path, source_name=None):
        """
        Import a transaction file in various formats (CSV, Excel, etc.)
        
        Args:
            file_path (str): Path to the file to import
            source_name (str, optional): Name of the source (e.g., "Chase Credit Card")
        
        Returns:
            bool: True if import was successful, False otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
            
        if source_name is None:
            source_name = file_path.stem
            
        logger.info(f"Importing transactions from {file_path}")
        
        try:
            # Determine file type by extension
            extension = file_path.suffix.lower()
            
            if extension == '.csv':
                df = self._import_csv(file_path)
            elif extension in ['.xlsx', '.xls']:
                df = self._import_excel(file_path)
            elif extension == '.qfx' or extension == '.ofx':
                df = self._import_ofx(file_path)
            elif extension == '.pdf':
                df = self._import_pdf(file_path)
            else:
                logger.error(f"Unsupported file format: {extension}")
                return False
                
            if df is None or df.empty:
                logger.error(f"No transactions found in {file_path}")
                return False
                
            # Add source information
            df['source'] = source_name
            df['import_date'] = datetime.now()
            df['file_path'] = str(file_path)
            
            # Add to master transactions DataFrame
            self.transactions = pd.concat([self.transactions, df], ignore_index=True)
            self.source_files.append(str(file_path))
            
            logger.info(f"Successfully imported {len(df)} transactions from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing {file_path}: {str(e)}", exc_info=True)
            return False
            
    def _import_csv(self, file_path):
        """
        Import transactions from a CSV file.
        
        Args:
            file_path (Path): Path to the CSV file
            
        Returns:
            pd.DataFrame: DataFrame with standardized transaction data
        """
        try:
            # Try to detect encoding and delimiter
            encoding = self._detect_encoding(file_path)
            delimiter = self._detect_delimiter(file_path, encoding)
            
            # Read CSV file
            df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding, error_bad_lines=False)
            
            # Try to identify the date, description, and amount columns
            return self._standardize_columns(df)
            
        except Exception as e:
            logger.error(f"Error importing CSV {file_path}: {str(e)}", exc_info=True)
            return None
    
    def _import_excel(self, file_path):
        """
        Import transactions from an Excel file.
        
        Args:
            file_path (Path): Path to the Excel file
            
        Returns:
            pd.DataFrame: DataFrame with standardized transaction data
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Try to identify the date, description, and amount columns
            return self._standardize_columns(df)
            
        except Exception as e:
            logger.error(f"Error importing Excel {file_path}: {str(e)}", exc_info=True)
            return None
    
    def _import_ofx(self, file_path):
        """
        Import transactions from an OFX/QFX file.
        
        Args:
            file_path (Path): Path to the OFX/QFX file
            
        Returns:
            pd.DataFrame: DataFrame with standardized transaction data
        """
        try:
            # This requires the ofxparse library
            import ofxparse
            
            with open(file_path, 'rb') as f:
                ofx = ofxparse.OfxParser.parse(f)
                
            # Extract account information
            account = ofx.account
            
            # Extract transactions
            transactions = []
            for transaction in account.statement.transactions:
                transactions.append({
                    'date': transaction.date,
                    'description': transaction.payee,
                    'amount': float(transaction.amount),
                    'transaction_id': transaction.id
                })
                
            # Create DataFrame
            df = pd.DataFrame(transactions)
            
            return df
            
        except ImportError:
            logger.error("ofxparse library not installed. Install with: pip install ofxparse")
            return None
        except Exception as e:
            logger.error(f"Error importing OFX/QFX {file_path}: {str(e)}", exc_info=True)
            return None
    
    def _import_pdf(self, file_path):
        """
        Import transactions from a PDF file.
        This is more complex and may require additional libraries like pdfplumber or tabula-py.
        
        Args:
            file_path (Path): Path to the PDF file
            
        Returns:
            pd.DataFrame: DataFrame with standardized transaction data
        """
        try:
            logger.warning("PDF import is experimental and may not work for all statement formats")
            
            # Try to use pdfplumber if available
            try:
                import pdfplumber
                
                transactions = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        # Extract tables from the page
                        tables = page.extract_tables()
                        
                        for table in tables:
                            # Process each table
                            if table and len(table) > 1:  # Ensure table has content
                                # Try to identify header row
                                header = table[0]
                                
                                # Check if this looks like a transaction table
                                if any('date' in str(col).lower() for col in header) and \
                                   any('amount' in str(col).lower() for col in header or \
                                       'transaction' in str(col).lower() for col in header):
                                    
                                    # Process data rows
                                    for row in table[1:]:
                                        # Try to extract date, description, and amount
                                        transactions.append(row)
                
                # If we found transactions, convert to DataFrame
                if transactions:
                    df = pd.DataFrame(transactions)
                    return self._standardize_columns(df)
                
            except ImportError:
                logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")
                
            # If pdfplumber failed or is not available, try tabula-py
            try:
                import tabula
                
                # Extract tables from PDF
                dfs = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
                
                # Combine all tables
                if dfs:
                    df = pd.concat(dfs, ignore_index=True)
                    return self._standardize_columns(df)
                
            except ImportError:
                logger.warning("tabula-py not installed. Install with: pip install tabula-py")
            
            logger.error(f"Failed to extract transactions from PDF {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error importing PDF {file_path}: {str(e)}", exc_info=True)
            return None
    
    def _detect_encoding(self, file_path):
        """
        Detect file encoding.
        
        Args:
            file_path (Path): Path to the file
            
        Returns:
            str: Detected encoding
        """
        try:
            import chardet
            
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read(1000))
            
            encoding = result['encoding']
            logger.debug(f"Detected encoding: {encoding}")
            return encoding
            
        except ImportError:
            logger.warning("chardet not installed. Using default encoding. Install with: pip install chardet")
            return BANK_IMPORT['default_encoding']
        except Exception:
            return BANK_IMPORT['default_encoding']
    
    def _detect_delimiter(self, file_path, encoding):
        """
        Detect CSV delimiter.
        
        Args:
            file_path (Path): Path to the CSV file
            encoding (str): File encoding
            
        Returns:
            str: Detected delimiter
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                sample = f.read(1000)
                
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
            
            logger.debug(f"Detected delimiter: {delimiter}")
            return delimiter
            
        except Exception:
            # Default to comma if detection fails
            return ','
    
    def _standardize_columns(self, df):
        """
        Standardize DataFrame columns to a common format.
        
        Args:
            df (pd.DataFrame): Raw transaction DataFrame
            
        Returns:
            pd.DataFrame: Standardized transaction DataFrame
        """
        # Make column names lowercase for easier matching
        df.columns = df.columns.str.lower()
        
        # Try to identify date column
        date_col = None
        for col in df.columns:
            if 'date' in col.lower():
                date_col = col
                break
                
        # Try to identify description/payee/merchant column
        desc_col = None
        for col in df.columns:
            if any(term in col.lower() for term in ['desc', 'payee', 'merchant', 'name', 'transaction']):
                desc_col = col
                break
                
        # Try to identify amount column
        amount_col = None
        for col in df.columns:
            if any(term in col.lower() for term in ['amount', 'sum', 'value', 'transaction', 'debit', 'credit']):
                amount_col = col
                break
                
        # If we couldn't identify all required columns, try to be smart
        if not all([date_col, desc_col, amount_col]):
            # Look at the data types
            for col in df.columns:
                # Check if column contains dates
                if not date_col and df[col].dtype == 'object':
                    try:
                        # Try to parse a sample as date
                        sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                        if sample and self._is_date(sample):
                            date_col = col
                            continue
                    except:
                        pass
                        
                # Check if column contains numeric values (could be amount)
                if not amount_col and df[col].dtype in ['float64', 'int64'] or (df[col].dtype == 'object' and self._contains_currency(df[col])):
                    amount_col = col
                    continue
                    
                # If we still don't have a description, use the first text column that's not a date
                if not desc_col and df[col].dtype == 'object' and col != date_col:
                    desc_col = col
        
        # If we still couldn't identify all required columns, return None
        if not all([date_col, desc_col, amount_col]):
            logger.error(f"Could not identify required columns. Found: date={date_col}, desc={desc_col}, amount={amount_col}")
            logger.debug(f"Available columns: {df.columns.tolist()}")
            return None
            
        # Create standardized DataFrame
        standardized = pd.DataFrame({
            'date': df[date_col],
            'description': df[desc_col],
            'amount': df[amount_col]
        })
        
        # Convert date to datetime
        standardized['date'] = self._parse_dates(standardized['date'])
        
        # Ensure amount is numeric
        standardized['amount'] = self._parse_amounts(standardized['amount'])
        
        # Add transaction_id column
        standardized['transaction_id'] = standardized.apply(
            lambda row: f"{row['date'].strftime('%Y%m%d')}-{hash(row['description']) % 10000:04d}-{abs(hash(str(row['amount']))) % 10000:04d}",
            axis=1
        )
        
        # Drop rows with missing values
        standardized.dropna(subset=['date', 'amount'], inplace=True)
        
        return standardized
    
    def _is_date(self, value):
        """Check if a value appears to be a date."""
        if isinstance(value, (datetime, pd.Timestamp)):
            return True
            
        if not isinstance(value, str):
            return False
            
        # Try parsing with various date formats
        for date_format in BANK_IMPORT['date_formats']:
            try:
                datetime.strptime(value, date_format)
                return True
            except ValueError:
                pass
                
        return False
    
    def _contains_currency(self, series):
        """Check if a series appears to contain currency values."""
        # Sample a few values
        sample = series.dropna().head(5).astype(str)
        
        # Check if they match currency pattern
        pattern = BANK_IMPORT['amount_regex']
        matches = sample.str.contains(pattern, regex=True)
        
        return matches.any()
    
    def _parse_dates(self, date_series):
        """
        Parse a series of dates into datetime objects.
        
        Args:
            date_series (pd.Series): Series of date values
            
        Returns:
            pd.Series: Series of datetime objects
        """
        # Try pandas built-in parsing first
        try:
            return pd.to_datetime(date_series, errors='coerce')
        except:
            pass
            
        # Try manual parsing with configured formats
        results = pd.Series([None] * len(date_series), index=date_series.index)
        
        for i, value in enumerate(date_series):
            if pd.isna(value):
                continue
                
            # Try each date format
            for date_format in BANK_IMPORT['date_formats']:
                try:
                    if isinstance(value, str):
                        dt = datetime.strptime(value, date_format)
                        results.iloc[i] = dt
                        break
                except ValueError:
                    continue
        
        return pd.to_datetime(results, errors='coerce')
    
    def _parse_amounts(self, amount_series):
        """
        Parse a series of amounts into numeric values.
        
        Args:
            amount_series (pd.Series): Series of amount values
            
        Returns:
            pd.Series: Series of numeric values
        """
        # If already numeric, just return
        if amount_series.dtype in ['float64', 'int64']:
            return amount_series
            
        # Convert to string first
        amount_series = amount_series.astype(str)
        
        # Function to parse individual amount strings
        def parse_amount(amount_str):
            if pd.isna(amount_str):
                return np.nan
                
            # Remove currency symbols and commas
            amount_str = re.sub(r'[,$£€]', '', str(amount_str))
            
            # Handle credits/debits notation
            if 'cr' in amount_str.lower():
                amount_str = amount_str.lower().replace('cr', '').strip()
                modifier = 1
            elif 'dr' in amount_str.lower():
                amount_str = amount_str.lower().replace('dr', '').strip()
                modifier = -1
            elif amount_str.startswith('(') and amount_str.endswith(')'):
                # Parentheses often indicate negative numbers
                amount_str = amount_str[1:-1].strip()
                modifier = -1
            elif amount_str.startswith('-'):
                modifier = 1  # Already negative
            else:
                modifier = 1
                
            # Extract numeric value
            match = re.search(r'-?\d+\.?\d*', amount_str)
            if match:
                try:
                    return float(match.group(0)) * modifier
                except ValueError:
                    return np.nan
            
            return np.nan
        
        # Apply parsing function
        parsed = amount_series.apply(parse_amount)
        
        # Handle positive/negative based on configuration
        if not BANK_IMPORT['positive_is_income']:
            parsed = -parsed
            
        return parsed
    
    def get_transactions(self, start_date=None, end_date=None, source=None):
        """
        Get transactions filtered by date range and/or source.
        
        Args:
            start_date (str or datetime, optional): Start date for filtering
            end_date (str or datetime, optional): End date for filtering
            source (str, optional): Filter by source name
            
        Returns:
            pd.DataFrame: Filtered transactions
        """
        if self.transactions.empty:
            return pd.DataFrame()
            
        # Apply date filters
        filtered = self.transactions.copy()
        
        if start_date:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            filtered = filtered[filtered['date'] >= start_date]
            
        if end_date:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            filtered = filtered[filtered['date'] <= end_date]
            
        # Apply source filter
        if source:
            filtered = filtered[filtered['source'] == source]
            
        return filtered.sort_values('date')
    
    def export_transactions(self, file_path):
        """
        Export transactions to a CSV file.
        
        Args:
            file_path (str): Path to save the CSV file
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        if self.transactions.empty:
            logger.warning("No transactions to export")
            return False
            
        try:
            self.transactions.to_csv(file_path, index=False)
            logger.info(f"Exported {len(self.transactions)} transactions to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting transactions: {str(e)}", exc_info=True)
            return False
    
    def deduplicate_transactions(self):
        """
        Remove duplicate transactions based on date, description, and amount.
        
        Returns:
            int: Number of duplicates removed
        """
        if self.transactions.empty:
            return 0
            
        # Count before deduplication
        count_before = len(self.transactions)
        
        # Remove duplicates
        self.transactions.drop_duplicates(
            subset=['date', 'description', 'amount'],
            keep='first',
            inplace=True
        )
        
        # Count after deduplication
        count_after = len(self.transactions)
        duplicates_removed = count_before - count_after
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate transactions")
            
        return duplicates_removed
    
    def summary(self):
        """
        Get a summary of imported transactions.
        
        Returns:
            dict: Summary statistics
        """
        if self.transactions.empty:
            return {
                'count': 0,
                'sources': [],
                'date_range': None
            }
            
        return {
            'count': len(self.transactions),
            'sources': self.transactions['source'].unique().tolist(),
            'date_range': {
                'start': self.transactions['date'].min().strftime('%Y-%m-%d'),
                'end': self.transactions['date'].max().strftime('%Y-%m-%d')
            },
            'total_income': self.transactions[self.transactions['amount'] > 0]['amount'].sum(),
            'total_expenses': self.transactions[self.transactions['amount'] < 0]['amount'].sum(),
            'net': self.transactions['amount'].sum()
        }