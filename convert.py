import os
import markdown

for file in ['Synopsis', 'SRS']:
    with open(f'docs/{file}.md', 'r', encoding='utf-8') as f:
        text = f.read()
        
    html_body = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    html = f'''<html><head><meta charset="utf-8"><style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 40px auto; line-height: 1.6; color: #333; }}
    h1, h2, h3 {{ color: #1e3a8a; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
    th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; }}
    th {{ background-color: #f8fafc; }}
    pre {{ background: #f1f5f9; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style></head><body>{html_body}</body></html>'''

    with open(f'docs/{file}.html', 'w', encoding='utf-8') as f:
        f.write(html)

print('Done!')
