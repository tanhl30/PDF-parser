import pdfplumber,pymupdf
import pandas as pd
import os , boto3, json
from pathlib import Path

"""use pdfplumber to extract text and table, use pymupdf to extract images and screenshots"""

def not_within_bboxes(obj, bboxes):
    """function to determine what content are NOT within the bounding boxes of the tables, used to filter out the table content in the text output"""
    def obj_in_bbox(_bbox):
        """See https://github.com/jsvine/pdfplumber/blob/stable/pdfplumber/table.py#L404"""
        v_mid = (obj["top"] + obj["bottom"]) / 2
        h_mid = (obj["x0"] + obj["x1"]) / 2
        x0, top, x1, bottom = _bbox
        return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)
    return not any(obj_in_bbox(__bbox) for __bbox in bboxes)

def is_valid_table(table):
    """Determines if the extracted structure looks like a valid table. A valid table typically has multiple rows with consistent columns."""
    col_count = len(table[0])
    row_count = len(table)
    
    if row_count<2 or col_count<2:
        return False
    else:
        for i in range(1,row_count):
            if len(table[i]) != col_count:
                return False
    return True

def extract_valid_tables(input_pdf, page, page_number,table_output_mode):
    """extract valid table as csv, invalid table as screenshot, record the location (coordinates) of the table extracted 
        Return : table_store : a list of tuple (table_label, table_data)
                screenshot_store : a list of tuple (table_label, screenshot)
                locations : a list of tuple (table_label, bbox)
    """
    tables = page.find_tables()
    table_store = []
    locations = []
    screenshot_store = []
    
    if table_output_mode == 'csv':
        for i, table in enumerate(tables):
            if is_valid_table(table.extract()):
                table_label = f"table_page_{page_number}_{i+1}"
                table_store.append((table_label, table.extract()))
                
            else:
                table_label = f"table_screenshot_page_{page_number}_{i+1}"
                screenshot_store.append((table_label,table_screenshot(input_pdf,page_number,table.bbox)))
                
            locations.append((f"<{table_label}>", table.bbox)) 
        return table_store,screenshot_store, locations
    
    elif table_output_mode == 'text':
        for i,table in enumerate(tables):
            if is_valid_table(table.extract()):
                table_label = f"<table_page_{page_number}_{i+1}>"
                table_content = '\n'.join([','.join(map(str, row)) for row in table.extract()])
                locations.append((table_content, table.bbox))

            else:
                table_label = f"table_screenshot_page_{page_number}_{i+1}"
                screenshot_store.append((table_label,table_screenshot(input_pdf,page_number,table.bbox)))
                locations.append((f"<{table_label}>", table.bbox)) 
        return screenshot_store, locations

    elif table_output_mode == 'bedrock':
        for i,table in enumerate(tables):
            if is_valid_table(table.extract()):
                table_label = f"<table_page_{page_number}_{i+1}>"
                table_content = table.extract()
                table_description = describe_table_content(table_content)
                locations.append((table_description, table.bbox))

            else:
                table_label = f"table_screenshot_page_{page_number}_{i+1}"
                screenshot_store.append((table_label,table_screenshot(input_pdf,page_number,table.bbox)))
                locations.append((f"<{table_label}>", table.bbox)) 
        return screenshot_store, locations

    else : print("Please select one of the following output mode: csv, text, bedrock")

def table_screenshot(pdf_file_path,page_number,bbox):
    """For table with weird structure, take a screenshot using the bounding box. 
        Return : Pixmap object from pymupdf
    """
    pdf = pymupdf.open(pdf_file_path)
    page = pdf.load_page(page_number)

    rect = pymupdf.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
    screenshot = page.get_pixmap(clip=rect)
    return screenshot

def extract_images(pdf_document):
    """extract images and record the image location"""
    images = []
    for page_index in range(len(pdf_document)):
        page = pdf_document[page_index]
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            img_rect = page.get_image_rects(xref)[0]
            coords = (img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)
            image_label = f"image_page_{page_index + 1}_{img_index + 1}"
            images.append((image_label, base_image, coords))
    return images

def save_output(data, output_dir, input_pdf, data_type):
    output_dir = Path(output_dir)
    base_name = Path(input_pdf).stem
    
    if data_type == 'text':
        txt_file = output_dir / f"{base_name}.txt"
        with txt_file.open('w', encoding="utf-8") as file:
            for page_number, page_elements in enumerate(data):
                file.write(f"--- Page {page_number+1} ---\n")
                for element, _ in page_elements:
                    if element.startswith('<') and element.endswith('>'):
                        file.write(f"{element}\n")
                    else:
                        file.write(f"{element} ")
                file.write("\n\n")
    
    elif data_type == 'table':
        for table_label, table_data in data:
            df = pd.DataFrame(table_data[1:], columns=table_data[0])
            csv_file = output_dir / f"{base_name}_{table_label}.csv"
            df.to_csv(csv_file, index=False)
    
    elif data_type == 'image':
        for img_label, img_data, _ in data:
            img_file = output_dir / f"{base_name}_{img_label}.{img_data['ext']}"
            with img_file.open('wb') as f:
                f.write(img_data["image"])
    
    elif data_type == 'screenshot':
        for img_label,screenshot in data:
            img_file = output_dir / f"{base_name}_{img_label}.png"
            screenshot.save(img_file)


def describe_table_content(table):
    """Convert a pdfplumber table to a description using AWS Bedrock."""
    table_content = '\n'.join([','.join(map(str, row)) for row in table])
    
    # Prepare the prompt
    prompt = f"""
    Context: Transform the table content into sentences. This will replace the table so it is important to include every cell's information

    Instruction: 
        1. Tansform the provided tables into a list of detailed and complete human-readable full sentences, ensuring that each cell's information is included.               
        2. Ensure that all necessary context, such as headers, table name, etc, can be derived for each individual sentence when read individually.
        3. In cases where common logic applies across multiple rows, please explicitly state all values instead of summarizing. Avoid unclear phrasing such as 'some', 'most','many'.
        4. Ensure completeness of information and output text without markdown.

    Table Content:
        {table_content}
    """
    
    # Initialize the Bedrock client
    bedrock_session = boto3.Session(region_name='us-east-1',profile_name='nonprod-appdev')
    bedrock = bedrock_session.client('bedrock-runtime')

    # Prepare the request body
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5,
        "top_p": 1
    })
    

    # Make the API call
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',  # or another appropriate model
        contentType='application/json',
        accept='application/json',
        body=body
    )

    # Parse and return the response
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


def extract_pdf(input_pdf, output_dir,table_output_mode):

    """ Extract image using pymupdf"""

    pdf_document = pymupdf.open(input_pdf)
    extracted_images = extract_images(pdf_document)
    pdf_document.close()
    save_output(extracted_images, output_dir, input_pdf, 'image')


    """ Extract text and table using pdfplumber,screenshot are handled by pymupdf"""

    final_text_locations = []
    with pdfplumber.open(input_pdf) as pdf:
        for page_number, page in enumerate(pdf.pages):

            #tables and screenshot are extracted
            if table_output_mode == 'csv':
                table_store, screenshot_store, locations = extract_valid_tables(input_pdf, page, page_number,'csv')
                save_output(table_store, output_dir, input_pdf, 'table')

            elif table_output_mode == 'text':
                screenshot_store, locations = extract_valid_tables(input_pdf, page, page_number,'text')          

            elif table_output_mode == 'bedrock':
                screenshot_store, locations = extract_valid_tables(input_pdf, page, page_number,'bedrock')



            save_output(screenshot_store, output_dir, input_pdf, 'screenshot')

            #Extract words and their positions, filtering out those within table bboxes
            bboxes = [location[1] for location in locations]
            words = page.extract_words(keep_blank_chars=False)
            filtered_words = [word for word in words if not_within_bboxes(word, bboxes)]

            #Append image location (coordinate) on this page
            for img_label, _, coords in extracted_images:
                if img_label.startswith(f"image_page_{page_number}_"):
                    locations.append((f"<{img_label}>", coords))
                
            #Append word location (coordinate) on this page
            locations.extend((word['text'], (word['x0'], word['top'], word['x1'], word['bottom'])) for word in filtered_words)

            #Sort all elements (table,image,screenshot,text) by their vertical position (top coordinate)
            locations.sort(key=lambda x: x[1][1])
            final_text_locations.append(locations)
                
                
        save_output(final_text_locations, output_dir, input_pdf, 'text')   


if __name__ == "__main__":
    input_pdf = "Your file path"
    output_directory = "Your output directory"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    extract_pdf(input_pdf, output_directory,'bedrock')