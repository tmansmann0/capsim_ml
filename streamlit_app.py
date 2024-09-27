import streamlit as st
import pandas as pd
import re

def main():
    st.title("Capstone Courier Data Extractor")

    st.write("Paste the raw data from the Capstone Courier report (pages 5 to 9):")

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
    # Split the raw data into pages
    pages = re.split(r'CAPSTONE® COURIER\s*Page \d+', raw_data)
    # Pages[1] is page 1, pages[2] is page 2, etc.

    data = []

    # Map page numbers to segments (adjusted for zero-based indexing)
    segment_pages = {
        5: "Traditional",
        6: "Low End",
        7: "High End",
        8: "Performance",
        9: "Size"
    }

    # Adjust page indices to match the pages list
    for page_num, segment in segment_pages.items():
        page_index = page_num  # Since pages[1] is Page 1
        if page_index < len(pages):
            page_data = pages[page_index]
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
    # First, find the line starting with 'Top Products in'
    lines = page_text.splitlines()
    header_line_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"Top Products in {segment} Segment"):
            # The header is likely in the next line(s)
            header_line_index = i + 1
            break

    if header_line_index is None:
        st.warning(f"Could not find products table in {segment} segment.")
        return []

    # Collect header lines until we have at least 15 columns
    headers = []
    while header_line_index < len(lines):
        header_line = lines[header_line_index]
        headers.extend(header_line.strip().split('\t'))
        header_line_index += 1
        if len(headers) >= 15:
            break

    # Now collect the product lines
    product_lines = []
    for line in lines[header_line_index:]:
        if line.strip() == '':
            continue
        if re.match(r'^\s*CAPSTONE® COURIER', line):
            break  # Reached end of page
        product_lines.append(line)

    # Now parse each product line
    products = []
    i = 0
    while i < len(product_lines):
        line = product_lines[i]
        # Split by tabs
        columns = line.strip().split('\t')
        # Check if there are enough columns
        if len(columns) < 15:
            # Try to combine with next line
            if i+1 < len(product_lines):
                next_line = product_lines[i+1]
                columns.extend(next_line.strip().split('\t'))
                i += 1  # Skip next line
            else:
                i += 1
                continue  # Cannot fix, skip this line
        if len(columns) < 15:
            i += 1
            continue  # Still insufficient columns

        (name, market_share, units_sold, revision_date, stock_out,
         pfmn_coord, size_coord, list_price, mtbf, age_dec31,
         promo_budget, cust_awareness, sales_budget, cust_accessibility,
         dec_cust_survey) = columns[:15]

        # Clean up data
        data_entry = {}
        data_entry['segment'] = segment
        data_entry['round'] = round_number
        data_entry['name'] = name.strip()
        data_entry['Market Share actual'] = market_share.strip().replace('%','')
        data_entry['units sold actual'] = units_sold.strip()
        data_entry['Revision Date'] = revision_date.strip()
        data_entry['stockout no/yes (0 or 1)'] = '0' if stock_out.strip() == '' else '1'
        data_entry['PMFT actual'] = pfmn_coord.strip()
        data_entry['size coordinate actual'] = size_coord.strip()
        data_entry['price actual'] = list_price.strip().replace('$','')
        data_entry['MTBF actual'] = mtbf.strip()
        data_entry['age actual'] = age_dec31.strip()
        data_entry['Promo Budget actual'] = promo_budget.strip().replace('$','').replace(',','')
        data_entry['awareness actual'] = cust_awareness.strip().replace('%','')
        data_entry['Sales Budget actual'] = sales_budget.strip().replace('$','').replace(',','')
        data_entry['accessibility actual'] = cust_accessibility.strip().replace('%','')
        data_entry['customer score actual'] = dec_cust_survey.strip()

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
        data_entry['Total Industry Unit Demand'] = total_industry_unit_demand
        products.append(data_entry)
        i += 1

    return products

if __name__ == '__main__':
    main()
