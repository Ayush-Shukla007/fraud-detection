import os
import re

def remove_emojis(text):
    emojis = ['🚨', '📊', '📉', '✅', '🛡️', '⚡', '🔍', '🔄', '🗑️', '⚠️', '📦', '📋', '📈', '👋', '👩‍💻', '⚙️', '✨']
    for e in emojis:
        text = text.replace(e, '')
    return text

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = remove_emojis(content)
    new_content = new_content.replace('FraudGuard AI', 'FraudGuard Pro')
    new_content = new_content.replace('Welcome back,', 'Overview:')
    new_content = new_content.replace('Account Trust Score', 'Risk Profile')
    new_content = new_content.replace('Quick Actions', 'Quick Analysis')
    new_content = new_content.replace('fraudguard-ai', 'fraudguard-pro')
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {filepath}')

frontend_src = r'C:\Users\ayush\Desktop\javascript\fraud-detection\frontend\src'
for root, _, files in os.walk(frontend_src):
    for file in files:
        if file.endswith('.jsx') or file.endswith('.js'):
            process_file(os.path.join(root, file))

# Fix index.html too
index_path = r'C:\Users\ayush\Desktop\javascript\fraud-detection\frontend\index.html'
if os.path.exists(index_path):
    process_file(index_path)

print('Done!')
