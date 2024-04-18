import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import base64
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import io
from openai import OpenAI
import json

# Initialize the Dash app with Bootstrap CSS
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Replace 'Your Key' with your actual OpenAI API key
client = OpenAI(api_key')


# Function to preprocess the image for better OCR results
def preprocess_image(image_content):
    img = Image.open(io.BytesIO(image_content))
    img = img.convert('L')  # Convert to grayscale
    img = ImageEnhance.Contrast(img).enhance(2)  # Enhance contrast
    img = img.point(lambda x: 0 if x < 128 else 255)  # Apply threshold
    img.save("/workspaces/ExpenseEase/preprocessed_image.jpg")
    return img

# Function to extract text from the image and then structure it using GPT-3
def extract_text_and_structure_with_gpt(image_content):
    img = preprocess_image(image_content)
    text = pytesseract.image_to_string(img, lang="eng")
    
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=f"Structure the following receipt text into a JSON format: {text}",
        max_tokens=1024,
        temperature=0
    )
    structured_text = response.choices[0].text.strip()

    return structured_text

# Dash app layout
app.layout = dbc.Container([
    dcc.Upload(
        id='upload-image',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px'
        },
        multiple=False,
        accept='image/png, image/jpeg'
    ),
    html.Div(id='output-image-upload'),
    html.Div(id='structured-data')
])

@app.callback(
    [Output('output-image-upload', 'children'),
     Output('structured-data', 'children')],
    [Input('upload-image', 'contents')]
)
def extract_and_parse(contents):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        structured_text = extract_text_and_structure_with_gpt(decoded)
        
        structured_data = json.loads(structured_text)  # Parse structured text as JSON
        
        # Assuming structured_data includes 'date' and 'items' keys
        date = structured_data.get('date', 'Date not found')
        items = structured_data.get('items', [])

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
                'minWidth': '80px', 'width': '80px', 'maxWidth': '80px',
                'whiteSpace': 'normal'
            },
            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold'
            }
        )
        return [html.Img(src=contents, style={'maxWidth': '100%', 'height': 'auto'}), items_table]
    return [None, None]

if __name__ == '__main__':
    app.run_server(debug=True)
