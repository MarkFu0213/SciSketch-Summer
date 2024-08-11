import pandas as pd

# Load the CSV file
input_file = 'science_direct_results.csv'
output_file = 'cell_journal_results.csv'

# Read the CSV file
df = pd.read_csv(input_file)

# Filter the DataFrame to keep only rows where sourceTitle is exactly "Cell"
cell_df = df[df['sourceTitle'] == 'Cell']

# Display some information about the filtered DataFrame
print(f"Total rows in original DataFrame: {len(df)}")
print(f"Rows with sourceTitle 'Cell': {len(cell_df)}")

# Display the first few rows of the filtered DataFrame
print("\nFirst few rows of the filtered DataFrame:")
print(cell_df.head())

# Save the filtered DataFrame to a new CSV file
cell_df.to_csv(output_file, index=False)
print(f"\nFiltered results saved to {output_file}")