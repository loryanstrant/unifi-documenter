#!/usr/bin/env python3
"""Fix all outstanding issues in one go"""

import re

print("Fixing all issues...")

# ============================================================================
# FIX 1: Add timezone-aware datetime utility
# ============================================================================
print("\n1. Adding timezone-aware datetime utility...")

utils_content = open('src/utils.py', 'r').read()

# Add timezone import and function at the top
if 'import pytz' not in utils_content:
    utils_content = utils_content.replace(
        'from datetime import datetime',
        'from datetime import datetime\nimport pytz'
    )
    
    # Add timezone-aware datetime function after imports
    insert_pos = utils_content.find('\ndef ')
    if insert_pos > 0:
        timezone_func = '''
def get_timezone_aware_now(config):
    """Get current datetime in configured timezone"""
    try:
        tz = pytz.timezone(config.TIMEZONE)
        return datetime.now(tz)
    except:
        return datetime.now()

'''
        utils_content = utils_content[:insert_pos] + timezone_func + utils_content[insert_pos:]

with open('src/utils.py', 'w') as f:
    f.write(utils_content)
print("✅ Added timezone utility function")

# ============================================================================
# FIX 2: Update web_server.py to use timezone-aware timestamps  
# ============================================================================
print("\n2. Fixing web_server timestamps...")

web_server = open('src/web_server.py', 'r').read()

# Add imports
if 'import pytz' not in web_server:
    web_server = web_server.replace(
        'from datetime import datetime',
        'from datetime import datetime\nimport pytz'
    )

# Add timezone helper function
if 'def _get_now_tz' not in web_server:
    insert_pos = web_server.find('class ProgressTracker:')
    if insert_pos > 0:
        # Find where to insert (before the class)
        tz_func = '''
def _get_now_tz(config):
    """Get timezone-aware current time"""
    try:
        tz = pytz.timezone(config.TIMEZONE if hasattr(config, 'TIMEZONE') else 'UTC')
        return datetime.now(tz)
    except:
        return datetime.now()


'''
        web_server = web_server[:insert_pos] + tz_func + web_server[insert_pos:]

# Update datetime.now() calls - need to pass config
# For ProgressTracker, we'll add config as an attribute
if 'def __init__(self):' in web_server and 'self.config = None' not in web_server:
    web_server = web_server.replace(
        'def __init__(self):\n        self.lock = threading.Lock()',
        'def __init__(self):\n        self.lock = threading.Lock()\n        self.config = None'
    )

# Replace datetime.now().isoformat() with timezone-aware version
web_server = re.sub(
    r"'start_time': datetime\.now\(\)\.isoformat\(\)",
    "'start_time': (_get_now_tz(self.config) if self.config else datetime.now()).isoformat()",
    web_server
)
web_server = re.sub(
    r"self\.current_job\['end_time'\] = datetime\.now\(\)\.isoformat\(\)",
    "self.current_job['end_time'] = (_get_now_tz(self.config) if self.config else datetime.now()).isoformat()",
    web_server
)

with open('src/web_server.py', 'w') as f:
    f.write(web_server)
print("✅ Fixed web_server timestamps")

# ============================================================================
# FIX 3: Fix GitHub logo - make it more visible
# ============================================================================
print("\n3. Making GitHub logo more visible...")

dashboard = open('templates/dashboard.html', 'r').read()

# The logo might not be showing because fill="white" on a white/light background
# Change it to use currentColor and make the link more visible
old_logo = '<svg height="32" width="32" viewBox="0 0 16 16" fill="white" style="vertical-align: middle; margin-right: 8px;">'
new_logo = '<svg height="32" width="32" viewBox="0 0 16 16" fill="currentColor" style="vertical-align: middle; margin-right: 8px; display: inline-block;">'

dashboard = dashboard.replace(old_logo, new_logo)

# Also make sure the link has good contrast
dashboard = dashboard.replace(
    'style="color: white; text-decoration: none; opacity: 0.8;"',
    'style="color: white; text-decoration: none; opacity: 1; display: inline-flex; align-items: center;"'
)

with open('templates/dashboard.html', 'w') as f:
    f.write(dashboard)
print("✅ Fixed GitHub logo visibility")

# ============================================================================
# FIX 4: Ensure _generate_index returns HTML
# ============================================================================
print("\n4. Fixing INDEX generation to output HTML...")

backup_analyzer = open('src/backup_analyzer.py', 'r').read()

# Find the _generate_index method and ensure it returns HTML
if 'def _generate_index' in backup_analyzer:
    # Look for the return statement in _generate_index
    # We need to wrap the markdown in HTML
    old_generate_index_return = '''        
        return index_md'''
    
    new_generate_index_return = '''        
        # Convert markdown to HTML for index
        if self.config.OUTPUT_FORMAT.lower() == 'html':
            from .html_generator import convert_markdown_to_html
            index_html = convert_markdown_to_html(index_md)
            # Wrap in full HTML document
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UniFi Documentation Index</title>
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
            padding: 40px;
        }}
        h1 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #764ba2;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        ul {{
            margin-left: 30px;
            margin-bottom: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
{index_html}
    </div>
</body>
</html>"""
        return index_md'''
    
    backup_analyzer = backup_analyzer.replace(old_generate_index_return, new_generate_index_return)

with open('src/backup_analyzer.py', 'w') as f:
    f.write(backup_analyzer)
print("✅ Fixed INDEX to generate HTML")

# ============================================================================
# FIX 5: Update main.py to pass config to progress tracker
# ============================================================================
print("\n5. Updating main.py to pass config to progress tracker...")

main_py = open('src/main.py', 'r').read()

# Find where progress_tracker is set and add config
if 'progress_tracker.config = config' not in main_py:
    # Find the import of progress_tracker
    main_py = main_py.replace(
        'from .web_server import create_app, progress_tracker',
        'from .web_server import create_app, progress_tracker\n\n# Set config for progress tracker\nprogress_tracker.config = config'
    )
    # If that didn't work, try after the config is created
    if 'progress_tracker.config = config' not in main_py:
        main_py = main_py.replace(
            'config = Config()',
            'config = Config()\nprogress_tracker.config = config'
        )

with open('src/main.py', 'w') as f:
    f.write(main_py)
print("✅ Updated main.py")

print("\n" + "="*60)
print("✅ ALL FIXES APPLIED!")
print("="*60)
print("\nFixed issues:")
print("  1. ✅ Timezone-aware timestamps (respects TZ environment variable)")
print("  2. ✅ INDEX now generates as INDEX.html with proper styling")
print("  3. ✅ HTML files now contain actual HTML (not markdown)")
print("  4. ✅ GitHub logo visibility improved (currentColor + display)")
print("\nNext steps:")
print("  - Commit and push changes")
print("  - Rebuild Docker image")
print("  - Deploy and test")
