import json
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import sys

def print_table(data, indent=0, is_top_level=False):
    output = []
    keys = list(data.keys())
    excluded_keys = {'path', 'guest_paths'}
    for i, key in enumerate(keys):
        if key in excluded_keys:
            continue
        value = data[key]
        prefix = "  " * indent
        if isinstance(value, dict):
            output.append(f"{prefix}{key}:")
            output += print_table(value, indent + 1).split('\n')
        elif isinstance(value, list):
            output.append(f"{prefix}{key}:")
            for item in value:
                output.append(f"{prefix}  - {item}")
        else:
            output.append(f"{prefix}{key}: {value}")
        
        if is_top_level and i < len(keys) - 1:
            output.append("")
    return "\n".join(filter(None, output))

def read_and_print_target_file_info(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        target_file_info = data.get("target", {}).get("file", {})
        if 'size' in target_file_info:
            target_file_info['size'] = str(target_file_info['size']) + " bytes"
        first_12_items = {k: target_file_info[k] for k in list(target_file_info)[:12]}
        return print_table(first_12_items, 0)

def read_and_print_capa_summary(file_path):
    excluded_keys = {'md5', 'sha1', 'sha256', 'path'}
    with open(file_path, 'r') as file:
        data = json.load(file)
        capa_summary = data.get("capa_summary", {})
        output = ["SUMMARY"]
        for key, value in capa_summary.items():
            if key in excluded_keys:
                continue
            output.append(f"{key}:")
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    output.append(f"    {sub_key}:")  
                    if isinstance(sub_value, list):
                        for item in sub_value:
                            output.append(f"        - {item}")  
                    else:
                        output.append(f"        {sub_value}") 
                output.append("-"*40)
            else:
                output.append(f"    {value}")  
                output.append("-"*40)
        return "\n".join(output)

def generate_report_header(file_path):
    match = re.search(r'(\d+)_report\.json', file_path)
    if match:
        report_number = match.group(1)
        header = f"MALWARE REPORT {report_number.zfill(4)}"
        return header
    else:
        return "Invalid file name format."


def write_to_pdf(file_path, content):
    base_name = re.sub(r'\.json$', '', file_path)
    c = canvas.Canvas(f"{base_name}.pdf", pagesize=letter)
    y_position = 750
    indent_width = 20  # Width of each indentation level
    max_width = 500  # Maximum width of text before wrapping

    for line in content.split('\n'):
        # Determine the level of indentation (number of leading spaces)
        indent_level = len(line) - len(line.lstrip(' '))
        x_position = 40 + (indent_level // 4 * indent_width)  # Adjust x based on indent level, assuming 4 spaces per indent level

        # Check for special headers or sections
        if line.strip().lower() == "summary":
            font_size = 14
            font = "Helvetica-Bold"
        elif line.startswith("MALWARE REPORT"):
            font_size = 14
            font = "Helvetica-Bold"
        else:
            font_size = 12
            font = "Helvetica"

        # Set font and write the line
        c.setFont(font, font_size)
        wrapped_lines = wrap_text(line.strip(), max_width, c, font, font_size)

        for wrapped_line in wrapped_lines:
            c.drawString(x_position, y_position, wrapped_line)
            y_position -= 14  # Adjust for font size and line spacing

            # Check if we need to start a new page
            if y_position <= 50:
                c.showPage()
                y_position = 750  # Reset y_position for the new page

    c.save()

def wrap_text(text, max_width, canvas, font, font_size):
    """
    Wraps text to fit into a specified width.
    """
    canvas.setFont(font, font_size)
    wrapped_lines = []
    words = text.split()
    current_line = ''

    for word in words:
        # Check if adding the next word exceeds the max width
        if canvas.stringWidth(current_line + ' ' + word, font, font_size) < max_width:
            current_line += ' ' + word if current_line else word
        else:
            # If the line is too wide, start a new line
            wrapped_lines.append(current_line)
            current_line = word

    # Add the last line if it's not empty
    if current_line:
        wrapped_lines.append(current_line)

    return wrapped_lines
    
def main():
    if len(sys.argv) != 2:
        print("Usage: <script_name>.exe <path_to_json_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    output_content = []

    output_content.append(generate_report_header(json_file_path))
    output_content.append(read_and_print_target_file_info(json_file_path))
    output_content.append("\n" + "-"*40 + "\n")
    output_content.append(read_and_print_capa_summary(json_file_path))

    final_output = "\n".join(filter(None, output_content))

    write_to_pdf(json_file_path, final_output)

if __name__ == "__main__":
    main()