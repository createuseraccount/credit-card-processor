def parse_transaction_line(line):
    """Parse a single line of transaction"""
    # Match date pattern (DD/MM/YY or DD/MM/YYYY)
    date_pattern = r"(\d{2}/\d{2}/(?:\d{2}|\d{4}))"
    # Match amount pattern (numbers with optional decimals and commas)
    amount_pattern = r"((?:Rs\.?|₹)?\s*[\d,]+\.?\d{0,2})"
    
    date_match = re.search(date_pattern, line)
    amount_match = re.search(amount_pattern, line)
    
    if date_match and amount_match:
        date = date_match.group(1)
        amount = amount_match.group(1)
        # Description is everything between date and amount
        description = line[date_match.end():amount_match.start()].strip()
        return [date, description, amount]
    return None

def process_credit_card_bill(df):
    """Process the extracted data"""
    if df is None or df.empty:
        return None
        
    # Remove any empty rows
    df = df.dropna(how='all')
    
    # Clean up amount format
    df['Amount'] = df['Amount'].str.replace(r'[^\d.-]', '', regex=True)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    # Clean up date format
    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        # If above fails, try with 2-digit year
        mask = df['Date'].isna()
        df.loc[mask, 'Date'] = pd.to_datetime(df.loc[mask, 'Date'], format='%d/%m/%y', errors='coerce')
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    except Exception as e:
        st.warning(f"Some dates could not be parsed: {str(e)}")
    
    # Remove rows where date or amount is invalid
    df = df.dropna(subset=['Date', 'Amount'])
    
    return df

def main():
    st.set_page_config(page_title="Credit Card Bill Processor", page_icon="💳")
    
    st.title("Credit Card Bill Processor")
    st.write("Convert your credit card bill PDF to Excel/CSV")
    
    # Add file size limit warning
    st.info("Maximum file size: 200MB")
    
    # File upload
    uploaded_file = st.file_uploader("Upload your credit card bill (PDF)", type=['pdf'])
    
    # Format selection
    format_type = st.radio("Select output format:", ('Excel', 'CSV'))
    
    if uploaded_file is not None:
        try:
            with st.spinner('Processing PDF... This may take a minute for scanned documents...'):
                # Try OCR extraction for scanned PDFs
                df = extract_from_scanned_pdf(uploaded_file)
                
                if df is not None and not df.empty:
                    df = process_credit_card_bill(df)
                    
                    if df is not None and not df.empty:
                        # Show preview
                        st.subheader("Preview of extracted data:")
                        st.dataframe(df.head())
                        
                        # Download button
                        st.markdown(get_download_link(df, format_type), unsafe_allow_html=True)
                        
                        # Display statistics
                        st.subheader("Summary Statistics:")
                        num_transactions = len(df)
                        st.write(f"Total number of transactions: {num_transactions}")
                        
                        if 'Amount' in df.columns:
                            total_amount = df['Amount'].sum()
                            st.write(f"Total amount: ₹{total_amount:,.2f}")
                    else:
                        st.error("Could not process the extracted data. Please check if the PDF contains valid transaction data.")
                else:
                    st.error("No transaction data found in the PDF. Please make sure you've uploaded a valid credit card statement.")
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.write("Please make sure you've uploaded a valid PDF file with transaction data.")

if __name__ == '__main__':
    main()
