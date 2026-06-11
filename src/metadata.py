import csv
import json
import random
from typing import List
from .scorer import ScoredCandidate
from .utils import logger

def generate_title(theme: str, part: int) -> str:
    templates = {
        "funny": [
            "Funniest Moments Caught on Camera #{part} #shorts",
            "You Won't Believe This #{part} #shorts",
            "Try Not To Laugh #{part} #shorts"
        ],
        "fishing": [
            "5 Fishing Moments That Look Unreal #{part} #shorts",
            "Monster Catch! #{part} #shorts",
            "Fishing Fails & Wins #{part} #shorts"
        ],
        "fails": [
            "Epic Fails of the Week #{part} #shorts",
            "What Were They Thinking? #{part} #shorts",
            "Ouch! That Gotta Hurt #{part} #shorts"
        ]
    }
    
    # Default to funny if theme not found
    theme_templates = templates.get(theme.lower(), templates["funny"])
    template = random.choice(theme_templates)
    return template.replace("{part}", str(part))

def generate_description(theme: str) -> str:
    return f"Check out this amazing {theme} moment! Don't forget to like and subscribe! #shorts #{theme}"

def export_metadata(candidates: List[ScoredCandidate], theme: str, reports_dir: str, shorts_dir: str):
    logger.info("Generating metadata reports...")
    
    metadata = []
    
    for i, cand in enumerate(candidates, start=1):
        title = generate_title(theme, i)
        desc = generate_description(theme)
        
        file_name = f"short_{i:03d}.mp4"
        
        meta = {
            "rank": i,
            "start_time": round(cand.candidate.start_time, 2),
            "end_time": round(cand.candidate.end_time, 2),
            "duration": round(cand.candidate.duration, 2),
            "score": round(cand.score, 2),
            "reason": cand.reason,
            "output_file": file_name,
            "suggested_title": title,
            "suggested_description": desc,
            "hashtags": f"#shorts #{theme}"
        }
        metadata.append(meta)
        
    # CSV
    csv_path = f"{reports_dir}/metadata.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if metadata:
            writer = csv.DictWriter(f, fieldnames=metadata[0].keys())
            writer.writeheader()
            writer.writerows(metadata)
            
    # JSON
    json_path = f"{reports_dir}/metadata.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    # HTML
    html_path = f"{reports_dir}/index.html"
    generate_html_report(metadata, html_path, shorts_dir)

def generate_html_report(metadata: List[dict], html_path: str, shorts_dir: str):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shorts Auto Cutter Report</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; }
            .short-card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; gap: 20px; }
            .video-container { width: 250px; flex-shrink: 0; }
            video { width: 100%; border-radius: 8px; }
            .info-container { flex-grow: 1; }
            h3 { margin-top: 0; color: #333; }
            .badge { background: #007bff; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .copy-btn { background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
            .copy-btn:hover { background: #218838; }
        </style>
    </head>
    <body>
        <h1>Shorts Generated</h1>
    """
    
    for item in metadata:
        # Use relative path from reports/ to shorts/
        video_rel_path = f"../shorts/{item['output_file']}"
        
        html_content += f"""
        <div class="short-card">
            <div class="video-container">
                <video controls>
                    <source src="{video_rel_path}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            <div class="info-container">
                <h3>Rank #{item['rank']} - {item['suggested_title']}</h3>
                <p><strong>Score:</strong> {item['score']}/10 <span class="badge">{item['reason']}</span></p>
                <p><strong>Time:</strong> {item['start_time']}s - {item['end_time']}s (Duration: {item['duration']}s)</p>
                <p><strong>Description:</strong><br><textarea id="desc-{item['rank']}" rows="3" style="width:100%;">{item['suggested_title']}\n\n{item['suggested_description']}</textarea></p>
                <button class="copy-btn" onclick="copyText('desc-{item['rank']}')">Copy Details</button>
            </div>
        </div>
        """
        
    html_content += """
        <script>
            function copyText(id) {
                var copyText = document.getElementById(id);
                copyText.select();
                copyText.setSelectionRange(0, 99999);
                navigator.clipboard.writeText(copyText.value);
                alert("Copied!");
            }
        </script>
    </body>
    </html>
    """
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
