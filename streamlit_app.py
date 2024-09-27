import streamlit as st
import pandas as pd
import re

def main():
    st.title("Capstone Courier Data Extractor")

    st.write("Paste the raw data from the Capstone Courier report:")

    raw_data = st.text_area("Raw Data", height=500)

    if st.button("Extract Data"):
        if raw_data:
            round_number = extract_round_number(raw_data)
            data = parse_data(raw_data, round_number)
            if data:
                df = pd.DataFrame(data)
                st.write("Extracted Data:")
                st.dataframe(df)
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "extracted_data.csv", "text/csv")
            else:
                st.error("No data extracted. Please check the raw data format.")
        else:
            st.error("Please paste the raw data.")

def extract_round_number(raw_data):
    match = re.search(r'Round:\s*(\d+)', raw_data)
    if match:
        return int(match.group(1))
    else:
        return None

def parse_data(raw_data, round_number):
    # Split the raw data into pages using page headers
    page_splits = re.split(r'CAPSTONE® COURIER.*?Page \d+', raw_data)
    page_headers = re.findall(r'(CAPSTONE® COURIER.*?Page \d+)', raw_data)
    pages = {}
    for i, header in enumerate(page_headers):
        page_number_match = re.search(r'Page (\d+)', header)
        if page_number_match:
            page_number = int(page_number_match.group(1))
            pages[page_number] = page_splits[i+1]  # i+1 because splits start after the header
    data = []

    # Map page numbers to segments
    segment_pages = {
        5: "Traditional",
        6: "Low End",
        7: "High End",
        8: "Performance",
        9: "Size"
    }

    for page_num, segment in segment_pages.items():
        if page_num in pages:
            page_data = pages[page_num]
            segment_data = parse_segment_page(page_data, segment, round_number)
            data.extend(segment_data)
        else:
            st.warning(f"Page {page_num} not found in the data.")
    return data

def parse_segment_page(page_text, segment, round_number):
    # Extract the Total Industry Unit Demand
    total_demand_match = re.search(r'Total Industry Unit Demand\s+([\d,]+)', page_text)
    if total_demand_match:
        total_industry_unit_demand = total_demand_match.group(1).replace(',', '')
    else:
        total_industry_unit_demand = ''

    # Extract the customer buying criteria
    criteria_pattern = r'(\d+)\.\s+([A-Za-z ]+)\s+([^\d%]+[^\d%])(\d+)%'
    criteria_matches = re.findall(criteria_pattern, page_text)

    criteria = {}
    for match in criteria_matches:
        number, criterion, expectation, importance = match
        criterion = criterion.strip()
        expectation = expectation.strip()
        importance = int(importance)
        criteria[criterion] = {'expectation': expectation, 'importance': importance}

    # Now extract the Top Products table
    lines = page_text.splitlines()
    header_line_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Top Products in"):
            # The header is likely in the next line(s)
            header_line_index = i + 1
            break

    if header_line_index is None:
        st.warning(f"Could not find products table in {segment} segment.")
        return []

    # Collect header lines until we have the correct headers
    headers = []
    while header_line_index < len(lines):
        header_line = lines[header_line_index].strip()
        if header_line == '':
            header_line_index += 1
            continue
        headers.extend(header_line.split('\t'))
        if 'Dec. Cust. Survey' in headers:
            break
        header_line_index += 1

    # Now collect the product lines
    product_lines = []
    for line in lines[header_line_index+1:]:
        if line.strip() == '':
            continue
        if re.match(r'^\s*CAPSTONE® COURIER', line) or line.strip().startswith("Perceptual Map"):
            break  # Reached end of page or next section
        product_lines.append(line.strip())

    # Now parse each product line
    products = []
    for line in product_lines:
        # Split by tabs
        columns = line.split('\t')
        if len(columns) < len(headers):
            continue  # Skip invalid lines

        product_data = dict(zip(headers, columns))

        # Clean up data
        data_entry = {}
        data_entry['segment'] = segment
        data_entry['round'] = round_number
        data_entry['Total Industry Unit Demand'] = total_industry_unit_demand
        data_entry['name'] = product_data.get('Name', '').strip()
        data_entry['Market Share actual'] = product_data.get('Market Share', '').strip().replace('%', '')
        data_entry['units sold actual'] = product_data.get('Units Sold to Seg', '').strip()
        data_entry['Revision Date'] = product_data.get('Revision\nDate', '').strip()
        stock_out = product_data.get('Stock Out', '').strip()
        data_entry['stockout no/yes (0 or 1)'] = '1' if stock_out else '0'
        data_entry['PMFT actual'] = product_data.get('Pfmn Coord', '').strip()
        data_entry['size coordinate actual'] = product_data.get('Size Coord', '').strip()
        data_entry['price actual'] = product_data.get('List\nPrice', '').strip().replace('$', '')
        data_entry['MTBF actual'] = product_data.get('MTBF', '').strip()
        data_entry['age actual'] = product_data.get('Age Dec.31', '').strip()
        data_entry['Promo Budget actual'] = product_data.get('Promo\nBudget', '').strip().replace('$', '').replace(',', '')
        data_entry['awareness actual'] = product_data.get('Cust. Aware-\nness', '').strip().replace('%', '')
        data_entry['Sales Budget actual'] = product_data.get('Sales\nBudget', '').strip().replace('$', '').replace(',', '')
        data_entry['accessibility actual'] = product_data.get('Cust. Access-\nibility', '').strip().replace('%', '')
        data_entry['customer score actual'] = product_data.get('Dec. Cust. Survey', '').strip()

        # Add criteria expectations and importance
        data_entry['age expectation'] = criteria.get('Age', {}).get('expectation', '')
        data_entry['age expectation importance'] = criteria.get('Age', {}).get('importance', '')
        price_expectation = criteria.get('Price', {}).get('expectation', '')
        price_range = re.findall(r'\$([0-9.]+)\s*-\s*\$?([0-9.]+)', price_expectation)
        if price_range:
            data_entry['price lower expectation'] = price_range[0][0]
            data_entry['price upper expectation'] = price_range[0][1]
        else:
            data_entry['price lower expectation'] = ''
            data_entry['price upper expectation'] = ''
        data_entry['price importance'] = criteria.get('Price', {}).get('importance', '')
        ideal_position = criteria.get('Ideal Position', {}).get('expectation', '')
        pfmn_match = re.search(r'Pfmn\s*([0-9.]+)', ideal_position)
        size_match = re.search(r'Size\s*([0-9.]+)', ideal_position)
        data_entry['Ideal Position PMFT'] = pfmn_match.group(1) if pfmn_match else ''
        data_entry['Ideal Position Size'] = size_match.group(1) if size_match else ''
        data_entry['Ideal Position Importance'] = criteria.get('Ideal Position', {}).get('importance', '')
        reliability_expectation = criteria.get('Reliability', {}).get('expectation', '')
        mtbf_range = re.findall(r'MTBF\s*([0-9]+)-([0-9]+)', reliability_expectation)
        if mtbf_range:
            data_entry['reliability MTBF lower limit'] = mtbf_range[0][0]
            data_entry['reliability MTBF upper limit'] = mtbf_range[0][1]
        else:
            data_entry['reliability MTBF lower limit'] = ''
            data_entry['reliability MTBF upper limit'] = ''
        products.append(data_entry)

    return products

if __name__ == '__main__':
    main()
