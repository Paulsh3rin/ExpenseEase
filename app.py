import dash
from dash import html, dcc, Input, Output, State
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import base64
from PIL import Image
import pytesseract
import re
import io

# Define a simple function to extract and parse text from images
def extract_text_from_image(image_content):
    img = Image.open(io.BytesIO(image_content))
    text = pytesseract.image_to_string(img, lang="eng")
    return text

def find_date(text):
    match = re.search(r'\d{2}/\d{2}/\d{4}', text)
    if match:
        return match.group()
    return None

def find_items(text):
    # Implement item extraction logic here
    return []

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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

def parse_contents(contents):
    return html.Div([
        html.Img(src=contents, style={'maxWidth': '100%', 'height': 'auto'}),
    ])

@app.callback(Output('output-image-upload', 'children'),
              Input('upload-image', 'contents'))
def update_output(contents):
    if contents is not None:
        children = parse_contents(contents)
        return children
    else:
        return None

@app.callback([Output('extracted-text', 'children'),
               Output('extracted-date', 'children'),
               Output('extracted-items', 'children')],
              Input('upload-image', 'contents'))
def extract_and_parse(contents):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        text = extract_text_from_image(decoded)
        date = find_date(text)
        items = find_items(text)
        return [html.P(f"Extracted Text: {text}"),
                html.P(f"Date: {date if date else 'Not found'}"),
                html.P(f"Items: {items if items else 'Not found'}")]
    return [None, None, None]

if __name__ == '__main__':
    app.run_server(debug=True)

