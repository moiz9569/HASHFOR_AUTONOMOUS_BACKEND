#!/usr/bin/env python3
"""
AI-Powered SEO Auto-Fix Agent - GENERIC VERSION FOR ANY WEBSITE
"""
import sys
import csv
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import openai  # OpenAI 0.28.1

# ---------------------------
# Environment Configuration
# ---------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_URL = os.getenv("REPO_URL")
BRANCH = os.getenv("BRANCH", "main")
SITE_BASE = os.getenv("SITE_BASE", "")
WORKDIR = Path("/tmp/seo-agent")
CSV_PATH = os.getenv("CSV_PATH", "seo_report.csv")
GIT_USERNAME = os.getenv("GIT_USERNAME", "SEO-Auto-Fix-Bot")
GIT_EMAIL = os.getenv("GIT_EMAIL", "seo-bot@example.com")

# Validate required environment variables
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY environment variable is required")
    sys.exit(1)

if not GITHUB_TOKEN or not REPO_URL:
    print("❌ GITHUB_TOKEN and REPO_URL environment variables are required")
    sys.exit(1)

# Inject token into repo URL (if provided)
if REPO_URL.startswith("https://") and "@" not in REPO_URL and GITHUB_TOKEN:
    REPO_URL = REPO_URL.replace("https://", f"https://{GITHUB_TOKEN}:x-oauth-basic@")

# Set OpenAI API key (0.28.1 style)
openai.api_key = OPENAI_API_KEY

# ---------------------------
# Helper Functions
# ---------------------------
def get_site_name(site_base: str) -> str:
    """Extract site name from site base URL"""
    try:
        parsed = urlparse(site_base)
        domain = parsed.netloc or parsed.path
        # Remove www. and get the main domain name
        domain = domain.replace('www.', '')
        # Extract the main part (e.g., "google" from "google.com")
        site_name = domain.split('.')[0]
        return site_name.title() if site_name else "Website"
    except:
        return "Website"

def get_domain_from_url(url: str) -> str:
    """Extract domain from any URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace('www.', '')
    except:
        return "website.com"

# ---------------------------
# Data structures
# ---------------------------
@dataclass
class Row:
    url: str
    title: str
    meta_description: str
    h1_count: Optional[int]
    heading_order: str
    missing_alt_tags: int
    total_images: int
    canonical_tag: str
    robots_meta: str
    viewport_present: str
    schema_types: str
    opengraph_tags: int
    twitter_tags: int
    word_count: int
    readability_score: float
    grammar_errors: int
    text_to_html_ratio: float
    top_keywords: str
    seo_score: int
    seo_suggestions: str

@dataclass
class Context:
    site_base: str
    repo_dir: Path
    stack: str
    url_to_file: Dict[str, Path]
    is_app_router: bool

# ---------------------------
# Helpers
# ---------------------------
def run(cmd: List[str], cwd: Optional[Path] = None) -> None:
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout)
    if result.stderr.strip():
        print(result.stderr)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)

def safe_write(file: Path, original: str, updated: Optional[str]):
    if not updated:
        print(f"⚠️ LLM failed, keeping original {file}")
        return
    lines = updated.splitlines()
    if len(lines) < len(original.splitlines()) * 0.5:
        print(f"⚠️ Suspiciously short output for {file}, keeping original")
        return
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(updated, encoding="utf-8")
    print(f"✅ File updated safely: {file}")

# ---------------------------
# OpenAI helpers - UPDATED FOR 0.28.1
# ---------------------------
def ask_openai(prompt: str, max_tokens: int = 500) -> str:
    try:
        # OpenAI 0.28.1 syntax
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use gpt-3.5-turbo for compatibility
            messages=[{"role": "system", "content": "You are an SEO assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI error:", e)
        return ""

def ai_parse_suggestions(suggestion_text: str, row: Row, site_base: str) -> Dict[str, object]:
    site_name = get_site_name(site_base)
    domain = get_domain_from_url(row.url)
    
    prompt = f"""
You are an SEO expert. Create optimized title and meta description for this page.
CURRENT DATA:
- Current Title: {row.title}
- Current Meta Description: {row.meta_description}
- URL: {row.url}
- Domain: {domain}
- Top Keywords: {row.top_keywords}
- SEO Suggestions: {row.seo_suggestions}
REQUIREMENTS:
- Title: 50-60 characters, include primary keywords, compelling
- Meta Description: 150-160 characters, include keywords, call-to-action
- Must be relevant to the page content
- Make it professional and engaging
Create a JSON response with the optimized title and meta description.
Output ONLY JSON in this format:
{{
  "new_title": "Optimized Title Here",
  "new_meta_description": "Optimized meta description here that is compelling and includes keywords."
}}
"""
    output = ask_openai(prompt)
    print(f"🤖 LLM raw output for {row.url}: {output}")
    
    try:
        # Clean the output
        output = re.sub(r",\s*}", "}", output)
        output = re.sub(r"```json\s*", "", output)
        output = re.sub(r"\s*```", "", output)
        
        suggestions = json.loads(output)
        
        # VALIDATION: Ensure title and description are not empty
        if not suggestions.get("new_title") or len(suggestions["new_title"].strip()) < 10:
            print("⚠️ AI returned empty/short title, using current title")
            suggestions["new_title"] = row.title or f"{site_name} - Professional Website"
        
        if not suggestions.get("new_meta_description") or len(suggestions["new_meta_description"].strip()) < 20:
            print("⚠️ AI returned empty/short description, using current description")
            suggestions["new_meta_description"] = row.meta_description or f"Explore {site_name} for professional services and information."
        
        print(f"✅ Final suggestions - Title: {suggestions['new_title']}")
        print(f"✅ Final suggestions - Description: {suggestions['new_meta_description']}")
        
        return suggestions
        
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        # FALLBACK: Use current data with improvements
        site_name = get_site_name(site_base)
        fallback_title = row.title or f"{site_name} - Professional Website"
        fallback_desc = row.meta_description or f"Explore {site_name} for professional services and information."
        
        return {
            "new_title": fallback_title,
            "new_meta_description": fallback_desc,
            "canonical": row.url,
        }

# ---------------------------
# CSV Parsing
# ---------------------------
def parse_csv(path: Path) -> List[Row]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                Row(
                    url=r["url"],
                    title=r.get("title", ""),
                    meta_description=r.get("meta_description", ""),
                    h1_count=int(r.get("h1_count", 0) or 0),
                    heading_order=r.get("heading_order", ""),
                    missing_alt_tags=int(r.get("missing_alt_tags", 0) or 0),
                    total_images=int(r.get("total_images", 0) or 0),
                    canonical_tag=r.get("canonical_tag", ""),
                    robots_meta=r.get("robots_meta", ""),
                    viewport_present=r.get("viewport_present", ""),
                    schema_types=r.get("schema_types", ""),
                    opengraph_tags=int(r.get("opengraph_tags", 0) or 0),
                    twitter_tags=int(r.get("twitter_tags", 0) or 0),
                    word_count=int(r.get("word_count", 0) or 0),
                    readability_score=float(r.get("readability_score", 0) or 0.0),
                    grammar_errors=int(r.get("grammar_errors", 0) or 0),
                    text_to_html_ratio=float(r.get("text_to_html_ratio", 0) or 0.0),
                    top_keywords=r.get("top_keywords", ""),
                    seo_score=int(r.get("seo_score", 0) or 0),
                    seo_suggestions=r.get("seo_suggestions", ""),
                )
            )
    return rows

# ---------------------------
# Repo + Stack Detection
# ---------------------------
def clone_repo():
    if WORKDIR.exists():
        shutil.rmtree(WORKDIR)
    run(["git", "clone", "-b", BRANCH, REPO_URL, str(WORKDIR)])

def detect_stack(repo_dir: Path) -> Tuple[str, bool]:
    if (repo_dir / "package.json").exists():
        content = (repo_dir / "package.json").read_text()
        if "next" in content:
            if (repo_dir / "app").exists() or (repo_dir / "src/app").exists():
                return "next", True
            return "next", False
    if (repo_dir / "_config.yml").exists():
        return "jekyll", False
    return "static", False

# ---------------------------
# File Mapping
# ---------------------------
def resolve_page_path(base_dir: str, url: str, repo_dir: Path, site_base: str) -> Path:
    """URL to file path conversion - FIXED VERSION"""
    
    # Remove protocol and normalize site_base
    if site_base.startswith(('http://', 'https://')):
        site_base_clean = site_base.split('://', 1)[1]
    else:
        site_base_clean = site_base
    
    # Remove protocol from URL and clean
    if url.startswith(('http://', 'https://')):
        url_clean = url.split('://', 1)[1]
    else:
        url_clean = url
    
    # Extract path after site base
    if url_clean.startswith(site_base_clean):
        path = url_clean[len(site_base_clean):].strip("/")
    else:
        # If site_base doesn't match, try to extract path directly
        path = url_clean.split('/', 1)[1] if '/' in url_clean else ""
    
    print(f"   🔍 URL Mapping: {url} -> clean_path: '{path}'")
    
    if not path:
        # Home page case
        candidates = ["page.tsx", "page.js", "page.jsx"]
        for c in candidates:
            candidate_path = repo_dir / base_dir / c
            if candidate_path.exists():
                print(f"   ✅ Found home page: {candidate_path}")
                return candidate_path
        default_home = repo_dir / base_dir / "page.js"
        print(f"   ⚠️ Using default home: {default_home}")
        return default_home

    # For nested pages
    page_folder = repo_dir / base_dir / path
    for ext in ["page.tsx", "page.js", "page.jsx"]:
        candidate = page_folder / ext
        if candidate.exists():
            print(f"   ✅ Found page: {candidate}")
            return candidate
    
    # Also check for index files (for pages router)
    for ext in ["index.tsx", "index.js", "index.jsx"]:
        candidate = page_folder / ext
        if candidate.exists():
            print(f"   ✅ Found index page: {candidate}")
            return candidate
    
    expected_path = page_folder / "page.js"
    print(f"   ❌ Page not found: {expected_path}")
    return expected_path

def map_urls_to_files(rows: List[Row], ctx: Context) -> Dict[str, Path]:
    mapping = {}
    print(f"🔍 Mapping URLs to files (Site Base: {ctx.site_base})")
    
    for row in rows:
        print(f"\n   📍 Processing URL: {row.url}")
        
        if ctx.stack == "next":
            if ctx.is_app_router:
                base_dir = "src/app" if (ctx.repo_dir / "src/app").exists() else "app"
            else:
                base_dir = "pages"
            
            target = resolve_page_path(base_dir, row.url, ctx.repo_dir, ctx.site_base)
            mapping[row.url] = target
            print(f"   🎯 Mapped to: {target}")
            
            if target.exists():
                print(f"   ✅ File exists: YES")
                content = target.read_text(encoding="utf-8")
                has_use_client = '"use client"' in content or "'use client'" in content
                has_metadata = "export const metadata" in content
                print(f"   📄 File Analysis:")
                print(f"      - Has 'use client': {has_use_client}")
                print(f"      - Has metadata: {has_metadata}")
            else:
                print(f"   ❌ File exists: NO")
    
    return mapping

# ---------------------------
# IMPROVED Metadata Builder - NOW WITH DYNAMIC SCHEMA
# ---------------------------
def build_metadata_block(suggestions: Dict, row: Row, site_base: str) -> str:
    """Generate a full Next.js metadata block including canonical, robots, and schema."""
    
    # Extract site information
    site_name = get_site_name(site_base)
    domain = get_domain_from_url(row.url)
    
    # --- Keywords cleanup ---
    keywords = []
    if row.top_keywords:
        raw_keywords = re.sub(r':\d+\.\d+%', '', row.top_keywords)
        parts = [k.strip() for k in re.split(r"[,\|;]", raw_keywords) if k.strip()]
        keywords = parts[:8]
    if not keywords:
        keywords = ["professional", "services", "website", "company", "business"]

    def esc(s: str) -> str:
        return s.replace('"', '\\"').replace("\n", " ").strip()

    # --- Basic SEO fields ---
    title = esc(suggestions.get("new_title", row.title or f"{site_name} - Professional Website"))
    desc = esc(suggestions.get("new_meta_description", row.meta_description or f"Explore {site_name} for professional services and information."))
    url = esc(row.url)
    canonical_url = esc(row.canonical_tag or row.url)
    robots_meta = esc(row.robots_meta or "index, follow")

    # --- OpenGraph / Twitter images ---
    og_image = f"{row.url.rstrip('/')}/opengraph-image.jpg"
    twitter_image = f"{row.url.rstrip('/')}/twitter-image.jpg"

    keywords_js = ",\n    ".join(f'"{esc(k)}"' for k in keywords)

    # --- DYNAMIC Schema.org JSON-LD ---
    # Use the schema type from CSV if available, otherwise determine based on URL
    schema_type = row.schema_types or "WebPage"
    
    # Base schema structure
    schema_data = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "url": row.url,
        "name": title,
        "description": desc,
    }
    
    # Add organization info for home page or if no specific schema type
    if not row.schema_types or row.schema_types == "WebPage":
        schema_data["publisher"] = {
            "@type": "Organization",
            "name": site_name,
            "url": site_base
        }
    
    # Convert to JSON
    schema_json = json.dumps(schema_data, indent=2)

    # --- Final Metadata Block ---
    return f"""// ✅ SEO Metadata
export const metadata = {{
  title: "{title}",
  description: "{desc}",
  keywords: [
    {keywords_js}
  ],
  alternates: {{
    canonical: "{canonical_url}"
  }},
  robots: "{robots_meta}",
  openGraph: {{
    title: "{title}",
    description: "{desc}",
    url: "{url}",
    siteName: "{site_name}",
    images: [
      {{
        url: "{og_image}",
        width: 1200,
        height: 630,
        alt: "{title}"
      }}
    ],
    type: "website"
  }},
  twitter: {{
    card: "summary_large_image",
    title: "{title}",
    description: "{desc}",
    images: ["{twitter_image}"]
  }}
}};

// ✅ Schema.org structured data (JSON-LD)
// Schema Type: {schema_type}
export const jsonLd = {schema_json};
"""

# ---------------------------
# Fixing Functions
# ---------------------------
def apply_next_fix(file: Path, suggestions: Dict, row: Row, is_app_router: bool, site_base: str):
    print(f"\n   🔧 Applying SEO fix to: {file}")
    
    if not file.exists():
        print(f"   ❌ SKIPPING - File does not exist: {file}")
        return

    original = file.read_text(encoding="utf-8")
    
    is_client_component = original.lstrip().startswith(('"use client"', "'use client'"))
    
    print(f"   📊 Component Analysis:")
    print(f"      - Is client component: {is_client_component}")
    print(f"      - Has existing metadata: {'export const metadata' in original}")
    
    if is_client_component:
        print(f"   ⚠️ SKIPPING - Client component: {file}")
        return

    # Server component - apply metadata
    metadata_block = build_metadata_block(suggestions, row, site_base)
    
    if re.search(r'export\s+const\s+metadata\s*=', original, re.DOTALL):
        print("   🔄 Replacing existing metadata")
        content = re.sub(r'export\s+const\s+metadata\s*=.*?;\n', metadata_block, original, flags=re.DOTALL)
    else:
        print("   ➕ Adding new metadata at top")
        content = metadata_block + "\n" + original

    content = content.replace("\r\n", "\n")
    safe_write(file, original, content)

# ---------------------------
# Commit & Push
# ---------------------------
def commit_and_push(ctx: Context):
    run(["git", "config", "user.name", GIT_USERNAME], cwd=ctx.repo_dir)
    run(["git", "config", "user.email", GIT_EMAIL], cwd=ctx.repo_dir)
    run(["git", "add", "."], cwd=ctx.repo_dir)
    try:
        run(["git", "commit", "-m", "chore(seo): auto-apply AI SEO suggestions"], cwd=ctx.repo_dir)
        print("✅ Changes committed successfully")
    except subprocess.CalledProcessError:
        print("ℹ️ No changes to commit.")
    run(["git", "push", "origin", BRANCH], cwd=ctx.repo_dir)

# ---------------------------
# Main
# ---------------------------
def main():
    print("🚀 Starting SEO Auto-Fix Agent - GENERIC VERSION")
    print("=" * 50)
    
    print("📥 Cloning repo...")
    clone_repo()

    print("🔎 Detecting stack...")
    stack, is_app_router = detect_stack(WORKDIR)
    print(f"✅ Stack: {stack}, AppRouter: {is_app_router}")

    print("📄 Parsing CSV...")
    rows = parse_csv(CSV_PATH)
    print(f"✅ Found {len(rows)} URLs in CSV")

    ctx = Context(site_base=SITE_BASE, repo_dir=WORKDIR, stack=stack, url_to_file={}, is_app_router=is_app_router)
    ctx.url_to_file = map_urls_to_files(rows, ctx)

    print(f"\n🎯 Processing {len(rows)} pages...")
    print("=" * 50)
    
    for i, row in enumerate(rows, 1):
        print(f"\n[{i}/{len(rows)}] 🔄 Processing: {row.url}")
        suggestions = ai_parse_suggestions(row.seo_suggestions, row, SITE_BASE)
        target = ctx.url_to_file.get(row.url)
        
        if not target:
            print(f"   ❌ No target file mapped for {row.url}")
            continue
            
        if stack == "next":
            apply_next_fix(target, suggestions, row, is_app_router, SITE_BASE)

    print("\n" + "=" * 50)
    print("🚀 Committing changes...")
    commit_and_push(ctx)
    print("✅ SEO Auto-Fix completed!")

if __name__ == "__main__":
    main()