import os
import subprocess
import sys
import tempfile
import gradio as gr
from pathlib import Path

# OpenAI API key is expected in environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY not set – AI features will fail")

def run_seo_fix(
    github_token: str,
    repo_url: str,
    branch: str,
    site_base: str,
    git_username: str,
    git_email: str,
    csv_file
) -> str:
    """
    Run the SEO auto-fix process.
    """
    if not OPENAI_API_KEY:
        return "❌ OPENAI_API_KEY not set. Please add it to your environment."

    # Validate inputs
    if not github_token or not repo_url or not site_base:
        return "❌ GitHub token, repository URL, and site base URL are required."

    # Handle CSV upload
    csv_path = None
    if csv_file is not None:
        # csv_file is a temporary file object from Gradio
        try:
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as f:
                # csv_file.name is the path to the uploaded file
                with open(csv_file.name, 'rb') as src:
                    f.write(src.read())
                csv_path = f.name
        except Exception as e:
            return f"❌ Error processing CSV file: {str(e)}"
    else:
        # Use default path if no CSV uploaded (main_script.py expects CSV_PATH)
        csv_path = "seo_report.csv"

    # Prepare environment for subprocess
    env = os.environ.copy()
    env.update({
        "GITHUB_TOKEN": github_token,
        "REPO_URL": repo_url,
        "BRANCH": branch,
        "SITE_BASE": site_base,
        "GIT_USERNAME": git_username,
        "GIT_EMAIL": git_email,
        "CSV_PATH": csv_path
    })

    try:
        # Run the main script
        proc = subprocess.run(
            [sys.executable, "main_script.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )

        output = f"Return code: {proc.returncode}\n"
        output += f"Success: {'✅' if proc.returncode == 0 else '❌'}\n\n"
        output += "STDOUT:\n" + proc.stdout + "\n"
        if proc.stderr:
            output += "STDERR:\n" + proc.stderr + "\n"

        # Clean up temp CSV if created
        if csv_path and csv_path.startswith(tempfile.gettempdir()):
            try:
                os.unlink(csv_path)
            except:
                pass

        return output

    except subprocess.TimeoutExpired:
        return "❌ Process timed out after 5 minutes."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# Build Gradio interface
with gr.Blocks(title="SEO Auto-Fix Agent") as demo:
    gr.Markdown("# 🚀 SEO Auto-Fix Agent")
    gr.Markdown("AI‑powered SEO optimization for your GitHub repositories")

    with gr.Row():
        with gr.Column(scale=1):
            github_token = gr.Textbox(
                label="GitHub Token",
                type="password",
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
                info="Create at GitHub Settings → Developer settings → Personal access tokens"
            )
            repo_url = gr.Textbox(
                label="Repository URL",
                placeholder="https://github.com/username/repository"
            )
            branch = gr.Textbox(
                label="Branch",
                value="main"
            )
            site_base = gr.Textbox(
                label="Site Base URL",
                placeholder="https://yoursite.com"
            )
            git_username = gr.Textbox(
                label="Git Username",
                value="SEO-Auto-Fix-Bot"
            )
            git_email = gr.Textbox(
                label="Git Email",
                value="seo-bot@example.com"
            )
            csv_file = gr.File(
                label="SEO Report CSV (optional)",
                file_types=[".csv"]
            )

            run_btn = gr.Button("🚀 Run SEO Auto-Fix", variant="primary")

        with gr.Column(scale=1):
            output = gr.Textbox(
                label="Output Log",
                lines=20,
                interactive=False,
                placeholder="Results will appear here..."
            )

    run_btn.click(
        fn=run_seo_fix,
        inputs=[
            github_token,
            repo_url,
            branch,
            site_base,
            git_username,
            git_email,
            csv_file
        ],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)






# from fastapi import FastAPI, Form, UploadFile, HTTPException, BackgroundTasks
# from fastapi.responses import JSONResponse, HTMLResponse
# from fastapi.middleware.cors import CORSMiddleware
# import os
# import subprocess
# import sys
# import tempfile
# import logging
# from typing import Optional

# # Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="SEO Auto-Fix Agent",
#     description="AI-powered SEO optimization for your GitHub repositories",
#     version="1.0.0"
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/", response_class=HTMLResponse)
# async def root():
#     """Serve a simple UI for the Space"""
#     return """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>SEO Auto-Fix Agent</title>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <style>
#             body { 
#                 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
#                 max-width: 800px; 
#                 margin: 0 auto; 
#                 padding: 20px; 
#                 background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                 min-height: 100vh;
#                 color: #333;
#             }
#             .container {
#                 background: white;
#                 padding: 30px;
#                 border-radius: 15px;
#                 box-shadow: 0 10px 30px rgba(0,0,0,0.2);
#             }
#             h1 { 
#                 color: #2c3e50; 
#                 text-align: center;
#                 margin-bottom: 10px;
#             }
#             .subtitle {
#                 text-align: center;
#                 color: #7f8c8d;
#                 margin-bottom: 30px;
#                 font-size: 1.1em;
#             }
#             .form-group { 
#                 margin-bottom: 20px; 
#             }
#             label { 
#                 display: block; 
#                 margin-bottom: 8px; 
#                 font-weight: 600;
#                 color: #2c3e50;
#             }
#             input, textarea { 
#                 width: 100%; 
#                 padding: 12px; 
#                 border: 2px solid #e1e8ed; 
#                 border-radius: 8px; 
#                 font-size: 16px;
#                 box-sizing: border-box;
#                 transition: border-color 0.3s;
#             }
#             input:focus, textarea:focus {
#                 outline: none;
#                 border-color: #667eea;
#             }
#             button { 
#                 background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                 color: white; 
#                 padding: 15px 30px; 
#                 border: none; 
#                 border-radius: 8px; 
#                 cursor: pointer; 
#                 font-size: 16px;
#                 font-weight: 600;
#                 width: 100%;
#                 transition: transform 0.2s;
#             }
#             button:hover { 
#                 transform: translateY(-2px);
#                 box-shadow: 0 5px 15px rgba(0,0,0,0.2);
#             }
#             .output { 
#                 background: #f8f9fa; 
#                 padding: 20px; 
#                 border-radius: 8px; 
#                 margin-top: 30px; 
#                 white-space: pre-wrap;
#                 font-family: 'Courier New', monospace;
#                 font-size: 14px;
#                 border-left: 4px solid #667eea;
#                 display: none;
#                 max-height: 400px;
#                 overflow-y: auto;
#             }
#             .success { border-left-color: #28a745; }
#             .error { border-left-color: #dc3545; }
#             .loading {
#                 text-align: center;
#                 color: #667eea;
#                 font-weight: 600;
#             }
#             .feature-list {
#                 display: grid;
#                 grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
#                 gap: 15px;
#                 margin: 20px 0;
#             }
#             .feature {
#                 background: #f8f9fa;
#                 padding: 15px;
#                 border-radius: 8px;
#                 text-align: center;
#                 border-left: 4px solid #667eea;
#             }
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <h1>🚀 SEO Auto-Fix Agent</h1>
#             <div class="subtitle">AI-powered SEO optimization for your GitHub repositories</div>
            
#             <div class="feature-list">
#                 <div class="feature">✅ AI-Optimized Titles</div>
#                 <div class="feature">✅ Meta Descriptions</div>
#                 <div class="feature">✅ Structured Data</div>
#                 <div class="feature">✅ OpenGraph Tags</div>
#             </div>
            
#             <form id="seoForm">
#                 <div class="form-group">
#                     <label for="github_token">🔑 GitHub Token:</label>
#                     <input type="password" id="github_token" name="github_token" required 
#                            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx">
#                     <small style="color: #666;">Create at: GitHub Settings → Developer settings → Personal access tokens</small>
#                 </div>
                
#                 <div class="form-group">
#                     <label for="repo_url">📁 Repository URL:</label>
#                     <input type="url" id="repo_url" name="repo_url" 
#                            placeholder="https://github.com/username/repository" required>
#                 </div>
                
#                 <div class="form-group">
#                     <label for="site_base">🌐 Site Base URL:</label>
#                     <input type="url" id="site_base" name="site_base" 
#                            placeholder="https://yoursite.com" required>
#                 </div>
                
#                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
#                     <div class="form-group">
#                         <label for="branch">🌿 Branch:</label>
#                         <input type="text" id="branch" name="branch" value="main">
#                     </div>
                    
#                     <div class="form-group">
#                         <label for="git_username">👤 Git Username:</label>
#                         <input type="text" id="git_username" name="git_username" value="SEO-Auto-Fix-Bot">
#                     </div>
#                 </div>
                
#                 <div class="form-group">
#                     <label for="git_email">📧 Git Email:</label>
#                     <input type="email" id="git_email" name="git_email" value="seo-bot@example.com">
#                 </div>
                
#                 <div class="form-group">
#                     <label for="csv_file">📊 SEO Report CSV (optional):</label>
#                     <input type="file" id="csv_file" name="csv_file" accept=".csv">
#                     <small style="color: #666;">Upload an SEO report CSV from tools like SiteBulb, Screaming Frog, etc.</small>
#                 </div>
                
#                 <button type="submit">🚀 Run SEO Auto-Fix</button>
#             </form>
            
#             <div id="output" class="output"></div>
#         </div>
        
#         <script>
#             document.getElementById('seoForm').addEventListener('submit', async (e) => {
#                 e.preventDefault();
#                 const output = document.getElementById('output');
#                 output.style.display = 'block';
#                 output.className = 'output loading';
#                 output.textContent = '🚀 Starting SEO auto-fix process...\\nPlease wait, this may take a few minutes...';
                
#                 const formData = new FormData(e.target);
                
#                 try {
#                     const response = await fetch('/run-seo-fix', {
#                         method: 'POST',
#                         body: formData
#                     });
                    
#                     const result = await response.json();
                    
#                     if (result.success) {
#                         output.className = 'output success';
#                     } else {
#                         output.className = 'output error';
#                     }
                    
#                     let outputText = `Return Code: ${result.returncode}\\n`;
#                     outputText += `Status: ${result.success ? 'SUCCESS 🎉' : 'COMPLETED WITH ERRORS ⚠️'}\\n\\n`;
#                     outputText += `STDOUT:\\n${result.stdout}\\n\\n`;
                    
#                     if (result.stderr) {
#                         outputText += `STDERR:\\n${result.stderr}\\n\\n`;
#                     }
                    
#                     outputText += `✅ Process completed! Check your GitHub repository for changes.`;
#                     output.textContent = outputText;
                    
#                 } catch (error) {
#                     output.className = 'output error';
#                     output.textContent = '❌ Error: ' + error.message + '\\n\\nPlease check your connection and try again.';
#                 }
#             });
#         </script>
#     </body>
#     </html>
#     """

# @app.get("/health")
# async def health_check():
#     return JSONResponse({"status": "healthy", "service": "SEO Auto-Fix Agent"})

# @app.post("/run-seo-fix")
# async def run_seo_fix(
#     background_tasks: BackgroundTasks,
#     github_token: str = Form(...),
#     repo_url: str = Form(...),
#     branch: str = Form("main"),
#     site_base: str = Form(...),
#     git_username: str = Form("SEO-Auto-Fix-Bot"),
#     git_email: str = Form("seo-bot@example.com"),
#     csv_file: Optional[UploadFile] = None
# ):
#     """Run SEO auto-fix process on a GitHub repository"""
#     logger.info("Starting SEO fix process...")
    
#     # Validate OpenAI API key
#     if not os.getenv("OPENAI_API_KEY"):
#         logger.error("OPENAI_API_KEY not set")
#         raise HTTPException(
#             status_code=500, 
#             detail="OPENAI_API_KEY not set. Please add it in Space settings -> Repository secrets"
#         )

#     # Create a temporary file for CSV if provided
#     csv_path = None
#     if csv_file and csv_file.filename and csv_file.filename.endswith('.csv'):
#         try:
#             with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as f:
#                 content = await csv_file.read()
#                 if not content:
#                     raise HTTPException(status_code=400, detail="CSV file is empty")
#                 f.write(content)
#                 csv_path = f.name
#                 logger.info(f"CSV file saved to: {csv_path}")
#         except Exception as e:
#             logger.error(f"Error processing CSV file: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")
#     else:
#         csv_path = "seo_report.csv"
#         logger.info("No CSV file provided, using default path")

#     # Prepare environment for subprocess
#     env = os.environ.copy()
#     env.update({
#         "GITHUB_TOKEN": github_token,
#         "REPO_URL": repo_url,
#         "BRANCH": branch,
#         "SITE_BASE": site_base,
#         "GIT_USERNAME": git_username,
#         "GIT_EMAIL": git_email,
#         "CSV_PATH": csv_path or "seo_report.csv"
#     })

#     try:
#         logger.info(f"Running SEO fix for repo: {repo_url}, branch: {branch}")
        
#         # Run main script with timeout
#         proc = subprocess.run(
#             [sys.executable, "main_script.py"],
#             env=env,
#             capture_output=True,
#             text=True,
#             timeout=300  # 5 minute timeout
#         )

#         response_data = {
#             "returncode": proc.returncode,
#             "stdout": proc.stdout,
#             "stderr": proc.stderr,
#             "success": proc.returncode == 0
#         }

#         logger.info(f"SEO fix process completed with return code: {proc.returncode}")

#         # Clean up temporary file in background
#         if csv_path and os.path.exists(csv_path) and "tmp" in csv_path:
#             background_tasks.add_task(cleanup_file, csv_path)

#         return response_data

#     except subprocess.TimeoutExpired:
#         logger.error("SEO fix process timed out after 5 minutes")
#         if csv_path and os.path.exists(csv_path) and "tmp" in csv_path:
#             background_tasks.add_task(cleanup_file, csv_path)
#         raise HTTPException(status_code=500, detail="SEO fix process timed out after 5 minutes")
#     except Exception as e:
#         logger.error(f"Error running SEO fix: {str(e)}")
#         if csv_path and os.path.exists(csv_path) and "tmp" in csv_path:
#             background_tasks.add_task(cleanup_file, csv_path)
#         raise HTTPException(status_code=500, detail=f"Error running SEO fix: {str(e)}")

# async def cleanup_file(file_path: str):
#     """Clean up temporary files"""
#     try:
#         if os.path.exists(file_path):
#             os.unlink(file_path)
#             logger.info(f"Cleaned up temporary file: {file_path}")
#     except Exception as e:
#         logger.warning(f"Failed to clean up file {file_path}: {e}")