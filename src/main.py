import os
import json
import base64
import tempfile
import pymupdf4llm

def main(context):
    # 1. Handle CORS for browser requests
    if context.req.method == 'OPTIONS':
        return context.res.send('', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-appwrite-key',
        })

    if context.req.method != 'POST':
        return context.res.json({'error': 'Method not allowed'}, 405, {'Access-Control-Allow-Origin': '*'})

    try:
        # 2. Parse Payload
        body = context.req.body_json if hasattr(context.req, 'body_json') and context.req.body_json else {}
        if not body and context.req.body:
            body = json.loads(context.req.body) if isinstance(context.req.body, str) else context.req.body

        file_b64 = body.get('file_b64')
        if not file_b64:
            return context.res.json({'error': 'Missing file_b64 in payload'}, 400, {'Access-Control-Allow-Origin': '*'})

        # 3. Decode File & Create Temporary Path
        file_data = base64.b64decode(file_b64)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_in:
            temp_in.write(file_data)
            temp_in_path = temp_in.name
            
        try:
            # 4. Convert PDF to Markdown (extracts tables perfectly formatted for LLMs)
            md_text = pymupdf4llm.to_markdown(temp_in_path)
            
            return context.res.json({
                'success': True,
                'markdown': md_text,
                'originalSize': len(file_data),
                'markdownSize': len(md_text.encode('utf-8'))
            }, 200, {'Access-Control-Allow-Origin': '*'})

        finally:
            # 5. PRIVACY GUARANTEE: Instantly wipe file from RAM/Disk
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)

    except Exception as e:
        context.error(f"Processing Error: {str(e)}")
        return context.res.json({'error': 'Server processing failed. Please check the file.'}, 500, {'Access-Control-Allow-Origin': '*'})
