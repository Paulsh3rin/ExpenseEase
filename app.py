import openai
import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import base64
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import re
import io

client = openai()

# Initialize your Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

openai.api_key = 'Your KEy'

# image pre-processing function
def preprocess_image(image_content):
    img = Image.open(io.BytesIO(image_content))
    img = img.convert('L')  # Convert to grayscale
    img = ImageEnhance.Contrast(img).enhance(2)  # Enhance contrast
    img = img.point(lambda x: 0 if x < 128 else 255)  # Apply threshold
    img.save("/workspaces/ExpenseEase/preprocessed_image.jpg")
    return img

# function to extract and parse text from images
def extract_text_from_image(image_content):
    img = preprocess_image(image_content)
    text = pytesseract.image_to_string(img, lang="eng")
    return text

# Extract Date
def find_date(text):
    date_patterns = [
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        r'\d{4}/\d{2}/\d{2}'   # YYYY/MM/DD
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return "Date not found"

# Extract Items
def find_items(text):
    item_pattern = re.compile(r'(?:(\d+)\s+)?(.*?)\s+(\d{1,3}(?:,\s?\d{3})*)')
    
    items = []
    for line in text.split('\n'):
        match = item_pattern.search(line)
        if match:
            quantity, description, price = match.groups()
            # Default quantity to 1 if not present
            quantity = quantity or '1'
            # Remove spaces from price to normalize it
            price = price.replace(', ', '').replace(',', '')
            items.append({'quantity': quantity, 'description': description.strip(), 'price': price})
    return items

# Define the function to call the OpenAI API
def structure_with_gpt(text):
    response = client.completions.create(
      model="gpt-3.5-turbo-instruct",
      prompt=f"Structure the following receipt text into a JSON format: {text}"
    )
    structured_text = response['choices'][0]['text'].strip()
    return structured_text

app.layout = dbc.Container([
    dcc.Upload(
        id='upload-image',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False,
        accept='image/png, image/jpeg'
    ),
    html.Div(id='output-image-upload'),
    html.Div(id='extracted-text'),
    html.Div(id='extracted-date'),
    html.Div(id='extracted-items')
])

@app.callback(
    [Output('output-image-upload', 'children'),
     Output('extracted-text', 'children'),
     Output('extracted-date', 'children'),
     Output('extracted-items', 'children')],
    [Input('upload-image', 'contents')]
)

def extract_and_parse(contents):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        text = extract_text_from_image(decoded)
        structured_text = structure_with_gpt(text)
        date = find_date(text)
        items = find_items(structured_text)

        # Format the extracted items for display in a Dash DataTable

        items_table = dash_table.DataTable(
            columns=[
                {'name': 'Quantity', 'id': 'quantity'},
                {'name': 'Description', 'id': 'description'},
                {'name': 'Price', 'id': 'price'}
            ],
            data=items,
            style_table={'overflowX': 'auto'},
            style_cell={
                'height': 'auto',
                # all three widths are needed
                'minWidth': '80px', 'width': '80px', 'maxWidth': '80px',
                'whiteSpace': 'normal'
            },
            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold'
            }
            )
        return [html.Img(src=contents, style={'maxWidth': '100%', 'height': 'auto'}),
                html.P(f"Extracted Text: {text}"),
                html.P(f"Date: {date}"),
                items_table]
    return [None, None, None, None]

if __name__ == '__main__':
    app.run_server(debug=True)

