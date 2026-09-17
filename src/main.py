import os
import json
import base64
import tempfile
import pymupdf4llm

def main(context):
    # Define who is allowed to talk to your server
    # ALLOWED_ORIGIN = 'https://elegxoai.in'
    
    if context.req.method == 'OPTIONS':
        return context.res.send('', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-appwrite-key',
        })

    if context.req.method != 'POST':
        return context.res.json({'error': 'Method not allowed'}, 405, {'Access-Control-Allow-Origin': '*'})

    try:
        body = context.req.body_json if hasattr(context.req, 'body_json') and context.req.body_json else {}
        if not body and context.req.body:
            body = json.loads(context.req.body) if isinstance(context.req.body, str) else context.req.body

        file_b64 = body.get('file_b64', '')
        if not file_b64:
            return context.res.json({'error': 'Missing file_b64 in payload'}, 400, {'Access-Control-Allow-Origin': '*'})

        # 1. Clean whitespace, line breaks, and Data-URI headers
        if ',' in file_b64:
            file_b64 = file_b64.split(',', 1)[1]
        file_b64 = ''.join(file_b64.split())

        # 2. Safe padding check
        remainder = len(file_b64) % 4
        if remainder == 1:
            # Drop the single orphaned character that prevents decoding
            file_b64 = file_b64[:-1]
        elif remainder > 1:
            file_b64 += '=' * (4 - remainder)

        # 3. Decode Base64
        try:
            file_data = base64.b64decode(file_b64)
        except Exception as b64_err:
            return context.res.json({'error': f'Invalid Base64 data: {str(b64_err)}'}, 400, {'Access-Control-Allow-Origin': '*'})

        # 4. Write to temp file and parse with PyMuPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_in:
            temp_in.write(file_data)
            temp_in_path = temp_in.name
            
        try:
            md_text = pymupdf4llm.to_markdown(temp_in_path)
            
            return context.res.json({
                'success': True,
                'markdown': md_text,
                'originalSize': len(file_data),
                'markdownSize': len(md_text.encode('utf-8'))
            }, 200, {'Access-Control-Allow-Origin': '*'})

        finally:
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)

    except Exception as e:
        context.error(f"Processing Error: {str(e)}")
        return context.res.json({'error': f"Conversion failed: {str(e)}"}, 500, {'Access-Control-Allow-Origin': '*'})
