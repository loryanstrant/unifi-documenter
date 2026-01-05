"""
HTML generation utilities for UniFi documentation
"""
import json
from typing import Dict, List, Any
from datetime import datetime


def generate_html_document(documentation: str, data: Dict, config_type: str, 
                          doc_hash: str, original_file: str) -> str:
    """Generate a complete HTML document with styling"""
    
    timestamp = datetime.now().isoformat()
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UniFi {config_type} Configuration - {doc_hash}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .metadata {{
            background: #f9f9f9;
            padding: 20px 40px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .metadata-item {{
            display: flex;
            flex-direction: column;
        }}
        .metadata-label {{
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .metadata-value {{
            font-weight: 600;
            color: #333;
        }}
        .content {{
            padding: 40px;
        }}
        .content h2 {{
            color: #667eea;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .content h3 {{
            color: #764ba2;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .content ul, .content ol {{
            margin-left: 30px;
            margin-bottom: 15px;
        }}
        .content li {{
            margin-bottom: 5px;
        }}
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .content th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .content td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .content tr:hover {{
            background: #f9f9f9;
        }}
        .content code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .content pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        .content pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        .footer {{
            background: #f9f9f9;
            padding: 20px 40px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.9em;
            color: #666;
        }}
        .tag {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-right: 10px;
            margin-bottom: 10px;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>UniFi {config_type} Configuration</h1>
            <p>Document ID: <code>{doc_hash}</code></p>
        </div>
        
        <div class="metadata">
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Configuration Type</div>
                    <div class="metadata-value">{config_type}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Document ID</div>
                    <div class="metadata-value">{doc_hash}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Generated</div>
                    <div class="metadata-value">{datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Original File</div>
                    <div class="metadata-value">{original_file}</div>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <span class="tag">{config_type}</span>
                {' '.join(f'<span class="tag">{key}</span>' for key in list(data.keys())[:5] if isinstance(data, dict))}
            </div>
        </div>
        
        <div class="content">
            {documentation}
        </div>
        
        <div class="footer">
            <p><strong>Generated by:</strong> UniFi Backup Analyzer</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>Data Keys:</strong> {', '.join(data.keys()) if isinstance(data, dict) else 'N/A'}</p>
        </div>
    </div>
</body>
</html>
"""


def generate_batch_html(doc_type: str, documents: List[Dict], documentation: str, 
                       files: List[str], timestamp: str) -> str:
    """Generate HTML for a batch of documents"""
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UniFi {doc_type.title()} Configuration Batch</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .stats {{
            background: #f9f9f9;
            padding: 30px 40px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .content {{
            padding: 40px;
        }}
        .content h2 {{
            color: #667eea;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .content h3 {{
            color: #764ba2;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .content ul, .content ol {{
            margin-left: 30px;
            margin-bottom: 15px;
        }}
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .content th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .content td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .content tr:hover {{
            background: #f9f9f9;
        }}
        .file-list {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .file-list h3 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        .file-item {{
            background: white;
            padding: 10px 15px;
            margin-bottom: 8px;
            border-radius: 4px;
            border-left: 3px solid #667eea;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .footer {{
            background: #f9f9f9;
            padding: 20px 40px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 UniFi {doc_type.title()} Configuration Batch</h1>
            <p>Comprehensive analysis of {len(documents)} related configurations</p>
        </div>
        
        <div class="stats">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(documents)}</div>
                    <div class="stat-label">Documents Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{doc_type.title()}</div>
                    <div class="stat-label">Configuration Type</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{datetime.fromisoformat(timestamp).strftime('%Y-%m-%d')}</div>
                    <div class="stat-label">Generated Date</div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <h2>📊 Batch Analysis</h2>
            {documentation}
            
            <div class="file-list">
                <h3>📁 Processed Files ({len(files)})</h3>
                {''.join(f'<div class="file-item">{i}. {file.split("/")[-1]}</div>' for i, file in enumerate(files, 1))}
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Generated by:</strong> UniFi Backup Analyzer</p>
            <p><strong>Batch Generated:</strong> {timestamp}</p>
            <p><strong>Document Type:</strong> {doc_type}</p>
            <p><strong>Total Files:</strong> {len(files)}</p>
        </div>
    </div>
</body>
</html>
"""


def convert_markdown_to_html(markdown_text: str) -> str:
    """Convert simple markdown to HTML (basic conversion)"""
    html = markdown_text
    
    # Headers
    html = html.replace('\n### ', '\n<h3>').replace('\n##', '\n<h2>').replace('\n# ', '\n<h1>')
    html = html.replace('</h1>\n', '</h1>').replace('</h2>\n', '</h2>').replace('</h3>\n', '</h3>')
    
    # Bold and italic
    import re
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    
    # Lists
    lines = html.split('\n')
    result_lines = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            result_lines.append(f'<li>{line.strip()[2:]}</li>')
        elif line.strip().startswith(tuple(f'{i}.' for i in range(10))):
            if not in_list:
                result_lines.append('<ol>')
                in_list = 'ol'
            result_lines.append(f'<li>{line.strip().split(".", 1)[1].strip()}</li>')
        else:
            if in_list:
                result_lines.append('</ol>' if in_list == 'ol' else '</ul>')
                in_list = False
            if line.strip():
                result_lines.append(f'<p>{line}</p>')
            else:
                result_lines.append('<br>')
    
    if in_list:
        result_lines.append('</ol>' if in_list == 'ol' else '</ul>')
    
    return '\n'.join(result_lines)
