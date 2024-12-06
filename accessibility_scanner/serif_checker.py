import re

bad_example = '<path_to_good_example>'
good_example = '<path_to_bad_example>'

def check_for_serif_fonts(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    serif_font_pattern = r"font-family:.*?\b([^;]*\bserif\b[^;]*)(?!sans-serif)"
    matches = re.findall(serif_font_pattern, content, re.IGNORECASE)
    
    serif_fonts = [match.strip() for match in matches if 'sans-serif' not in match.lower()]
    
    if serif_fonts:
        print(f"Found serif fonts in {file_path}:")
        # for font in serif_fonts:
        #     print(f"- {font}\n")
    else:
        print(f"No serif fonts found in {file_path}.")

check_for_serif_fonts(bad_example)
check_for_serif_fonts(good_example)