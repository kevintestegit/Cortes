import csv
import html
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
            "viral_score": round(cand.viral_score, 1),
            "hook_score": round(cand.hook_score, 1),
            "retention_score": round(cand.retention_score, 1),
            "action_score": round(cand.action_score, 1),
            "sound_score": round(cand.sound_score, 1),
            "viral_label": cand.viral_label,
            "viral_tip": cand.viral_tip,
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

def _badge_class(score: float) -> str:
    if score >= 82:
        return "high"
    if score >= 68:
        return "good"
    if score >= 52:
        return "test"
    return "low"

def generate_html_report(metadata: List[dict], html_path: str, shorts_dir: str):
    top_rows = ""
    for item in metadata[:10]:
        cls = _badge_class(float(item["viral_score"]))
        top_rows += f"""
            <tr>
                <td>#{item['rank']}</td>
                <td><strong>{item['viral_score']}/100</strong></td>
                <td><span class="priority {cls}">{html.escape(str(item['viral_label']))}</span></td>
                <td>{item['duration']}s</td>
                <td>{html.escape(str(item['suggested_title']))}</td>
                <td>{html.escape(str(item['viral_tip']))}</td>
            </tr>
        """

    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shorts Auto Cutter - Ranking Viral</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #1d1d1f; padding: 20px; }
            .summary { background: white; border-radius: 8px; padding: 18px; margin-bottom: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); }
            .summary h2 { margin-top: 0; }
            table { width: 100%; border-collapse: collapse; }
            th, td { text-align: left; border-bottom: 1px solid #e2e2e8; padding: 10px 8px; vertical-align: top; }
            th { font-size: 13px; color: #555; }
            .short-card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; gap: 20px; }
            .video-container { width: 250px; flex-shrink: 0; }
            video { width: 100%; border-radius: 8px; }
            .info-container { flex-grow: 1; }
            h3 { margin-top: 0; color: #333; }
            .badge, .priority { color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; display: inline-block; }
            .badge { background: #007bff; }
            .priority.high { background: #15803d; }
            .priority.good { background: #2563eb; }
            .priority.test { background: #b45309; }
            .priority.low { background: #6b7280; }
            .metrics { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
            .metric { background: #f0f2f5; border-radius: 6px; padding: 7px 9px; font-size: 13px; }
            .copy-btn { background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
            .copy-btn:hover { background: #218838; }
            textarea { font-family: Consolas, monospace; min-height: 74px; }
            @media (max-width: 760px) {
                .short-card { display: block; }
                .video-container { width: 100%; max-width: 320px; margin-bottom: 14px; }
                table { font-size: 13px; }
            }
        </style>
    </head>
    <body>
        <h1>Ranking Viral dos Shorts</h1>
        <div class="summary">
            <h2>Ordem recomendada para postar</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Viral</th>
                        <th>Prioridade</th>
                        <th>Duracao</th>
                        <th>Titulo sugerido</th>
                        <th>Uso</th>
                    </tr>
                </thead>
                <tbody>__TOP_ROWS__</tbody>
            </table>
        </div>
    """
    html_content = html_content.replace("__TOP_ROWS__", top_rows)
    
    for item in metadata:
        # Use relative path from reports/ to shorts/
        video_rel_path = f"../shorts/{item['output_file']}"
        cls = _badge_class(float(item["viral_score"]))
        title = html.escape(str(item["suggested_title"]))
        desc = html.escape(str(item["suggested_description"]))
        reason = html.escape(str(item["reason"]))
        label = html.escape(str(item["viral_label"]))
        tip = html.escape(str(item["viral_tip"]))
        
        html_content += f"""
        <div class="short-card">
            <div class="video-container">
                <video controls>
                    <source src="{video_rel_path}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            <div class="info-container">
                <h3>Rank #{item['rank']} - {title}</h3>
                <p><strong>Viral score:</strong> {item['viral_score']}/100 <span class="priority {cls}">{label}</span></p>
                <div class="metrics">
                    <span class="metric">Hook: {item['hook_score']}/100</span>
                    <span class="metric">Retencao: {item['retention_score']}/100</span>
                    <span class="metric">Acao: {item['action_score']}/100</span>
                    <span class="metric">Audio: {item['sound_score']}/100</span>
                    <span class="metric">Score tecnico: {item['score']}/10</span>
                </div>
                <p><strong>Motivo:</strong> <span class="badge">{reason}</span></p>
                <p><strong>Recomendacao:</strong> {tip}</p>
                <p><strong>Time:</strong> {item['start_time']}s - {item['end_time']}s (Duration: {item['duration']}s)</p>
                <p><strong>Descricao:</strong><br><textarea id="desc-{item['rank']}" rows="4" style="width:100%;">{title}

{desc}
{html.escape(str(item['hashtags']))}</textarea></p>
                <button class="copy-btn" onclick="copyText('desc-{item['rank']}')">Copiar texto</button>
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
