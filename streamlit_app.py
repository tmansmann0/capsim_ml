import streamlit as st
import pandas as pd
import re

def main():
    st.title("Capstone Courier Data Extractor")

    st.write("Paste the raw data from the Capstone Courier report (pages 5 to 9):")

    raw_data = st.text_area("Raw Data", height=500)

    if st.button("Extract Data"):
        if raw_data:
            data = parse_data(raw_data)
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

def parse_data(raw_data):
    # Split the raw data into pages
    pages = re.split(r'CAPSTONE® COURIER\s*Page \d+', raw_data)
    # Pages[0] is header, pages[1] is page 1, etc.

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
        if page_num < len(pages):
            page_data = pages[page_num]
            segment_data = parse_segment_page(page_data, segment)
            data.extend(segment_data)
        else:
            st.warning(f"Page {page_num} not found in the data.")
    return data

def parse_segment_page(page_text, segment):
    # Extract the customer buying criteria
    criteria_pattern = r'(\d+)\.\s+([A-Za-z ]+)\s+([^%]+)\s+(\d+)%'
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
        if line.startswith("Name\tMarket Share\tUnits Sold to Seg"):
            header_line_index = i
            break

    if header_line_index is None:
        st.warning(f"Could not find products table in {segment} segment.")
        return []

    # Now parse the product data
    product_lines = []
    for line in lines[header_line_index+1:]:
        if line.strip() == '':
            continue
        if re.match(r'^\s*CAPSTONE® COURIER', line):
            break  # Reached end of page
        product_lines.append(line)

    # Now parse each product line
    products = []
    for line in product_lines:
        # Split by tabs
        columns = line.split('\t')
        if len(columns) < 15:
            continue  # Skip invalid lines

        (name, market_share, units_sold, revision_date, stock_out,
         pfmn_coord, size_coord, list_price, mtbf, age_dec31,
         promo_budget, cust_awareness, sales_budget, cust_accessibility,
         dec_cust_survey) = columns[:15]

        # Clean up data
        data_entry = {}
        data_entry['segment'] = segment
        data_entry['round'] = 0  # Assuming round 0, or extract from data if available
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
        products.append(data_entry)

    return products

if __name__ == '__main__':
    main()
