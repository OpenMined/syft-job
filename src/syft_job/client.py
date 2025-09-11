import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from .config import SyftJobConfig


class JobInfo:
    """Information about a job with approval capabilities."""
    
    def __init__(self, name: str, user: str, status: str, submitted_by: str, location: Path, config: SyftJobConfig):
        self.name = name
        self.user = user
        self.status = status
        self.submitted_by = submitted_by
        self.location = location
        self._config = config
    
    def __str__(self) -> str:
        status_emojis = {"inbox": "📥", "approved": "✅", "done": "🎉"}
        emoji = status_emojis.get(self.status, "❓")
        return f"{emoji} {self.name} ({self.status}) -> {self.user}"
    
    def __repr__(self) -> str:
        return f"JobInfo(name='{self.name}', user='{self.user}', status='{self.status}')"
    
    def accept_by_depositing_result(self, file_path: str) -> Path:
        """
        Accept a job by depositing the result file and moving it to done status.
        
        Args:
            file_path: Path to the result file to deposit
            
        Returns:
            Path to the deposited result file
            
        Raises:
            ValueError: If job is not in inbox status
            FileNotFoundError: If the result file doesn't exist
        """
        if self.status != "inbox":
            raise ValueError(f"Job '{self.name}' is not in inbox status (current: {self.status})")
        
        result_file = Path(file_path)
        if not result_file.exists():
            raise FileNotFoundError(f"Result file not found: {file_path}")
        
        # Prepare done directory path
        done_dir = self._config.get_done_dir(self.user) / self.name
        
        # Ensure the parent done directory exists, but not the job directory itself
        done_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the job from inbox to done
        shutil.move(str(self.location), str(done_dir))
        
        # Create outputs directory in the done job
        outputs_dir = done_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        # Copy the result file to outputs directory
        result_filename = result_file.name
        destination = outputs_dir / result_filename
        shutil.copy2(str(result_file), str(destination))
        
        # Update this object's state
        self.status = "done"
        self.location = done_dir
        
        return destination


class JobsList:
    """A list-like container for JobInfo objects with nice display."""
    
    def __init__(self, jobs: List[JobInfo], root_email: str):
        self._jobs = jobs
        self._root_email = root_email
    
    def __getitem__(self, index) -> JobInfo:
        return self._jobs[index]
    
    def __len__(self) -> int:
        return len(self._jobs)
    
    def __iter__(self):
        return iter(self._jobs)
    
    def __str__(self) -> str:
        """Format jobs list as a nice table."""
        if not self._jobs:
            return "📭 No jobs found.\n"
        
        # Calculate column widths
        name_width = max(len(job.name) for job in self._jobs) + 2
        status_width = max(len(job.status) for job in self._jobs) + 2
        
        # Ensure minimum widths
        name_width = max(name_width, 15)
        status_width = max(status_width, 12)
        
        # Status emojis
        status_emojis = {
            "inbox": "📥",
            "approved": "✅", 
            "done": "🎉"
        }
        
        # Build table
        lines = []
        lines.append(f"📊 Jobs for {self._root_email}")
        lines.append("=" * (name_width + status_width + 15))
        
        # Header
        header = f"{'Index':<6} {'Job Name':<{name_width}} {'Status':<{status_width}}"
        lines.append(header)
        lines.append("-" * len(header))
        
        # Sort jobs by status priority (inbox, approved, done) then by name
        status_priority = {"inbox": 1, "approved": 2, "done": 3}
        sorted_jobs = sorted(self._jobs, key=lambda j: (status_priority.get(j.status, 4), j.name.lower()))
        
        # Job rows
        for i, job in enumerate(sorted_jobs):
            emoji = status_emojis.get(job.status, "❓")
            status_display = f"{emoji} {job.status}"
            line = f"[{i:<4}] {job.name:<{name_width}} {status_display:<{status_width}}"
            lines.append(line)
        
        lines.append("")
        lines.append(f"📈 Total: {len(self._jobs)} jobs")
        
        # Status summary
        status_counts = {}
        for job in self._jobs:
            status_counts[job.status] = status_counts.get(job.status, 0) + 1
        
        summary_parts = []
        for status, count in status_counts.items():
            emoji = status_emojis.get(status, "❓")
            summary_parts.append(f"{emoji} {count} {status}")
        
        if summary_parts:
            lines.append("📋 " + " | ".join(summary_parts))
        
        lines.append("")
        lines.append("💡 Use job_client.jobs[0].accept_by_depositing_result('file.txt') to approve jobs")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"JobsList({len(self._jobs)} jobs)"
    
    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks with enhanced visual appeal."""
        if not self._jobs:
            return """
            <style>
                @keyframes syftjob-pulse {
                    0% { opacity: 0.6; transform: scale(0.98); }
                    50% { opacity: 1; transform: scale(1); }
                    100% { opacity: 0.6; transform: scale(0.98); }
                }
                
                .syftjob-empty {
                    padding: 40px 30px; 
                    text-align: center; 
                    border-radius: 16px; 
                    background: linear-gradient(135deg, #f8c073 0%, #f79763 50%, #cc677b 100%);
                    border: 1px solid rgba(248,192,115,0.3);
                    box-shadow: 0 8px 32px rgba(248,192,115,0.3);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                    color: white;
                }
                
                .syftjob-empty::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                    animation: syftjob-shine 3s infinite;
                }
                
                @keyframes syftjob-shine {
                    0% { left: -100%; }
                    100% { left: 100%; }
                }
                
                .syftjob-empty h3 { 
                    margin: 0 0 12px 0; 
                    font-size: 24px;
                    color: white;
                    font-weight: 700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }
                
                .syftjob-empty p { 
                    margin: 0; 
                    color: rgba(255,255,255,0.9); 
                    font-size: 16px;
                    opacity: 0.95;
                }
                
                .syftjob-empty-icon {
                    font-size: 48px;
                    margin-bottom: 20px;
                    display: block;
                    animation: syftjob-pulse 2s infinite;
                }
                
                /* Dark theme */
                @media (prefers-color-scheme: dark) {
                    .syftjob-empty {
                        background: linear-gradient(135deg, #937098 0%, #6976ae 50%, #52a8c5 100%);
                        border-color: rgba(147,112,152,0.4);
                        box-shadow: 0 8px 32px rgba(147,112,152,0.4);
                    }
                    .syftjob-empty::before {
                        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                    }
                    .syftjob-empty h3 { 
                        color: white;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                    }
                    .syftjob-empty p { 
                        color: rgba(255,255,255,0.95); 
                        opacity: 0.95;
                    }
                }
                
                /* Jupyter dark theme detection */
                .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-empty,
                body[data-jp-theme-light="false"] .syftjob-empty {
                    background: linear-gradient(135deg, #937098 0%, #6976ae 50%, #52a8c5 100%);
                    border-color: rgba(147,112,152,0.4);
                    box-shadow: 0 8px 32px rgba(147,112,152,0.4);
                }
                .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-empty::before,
                body[data-jp-theme-light="false"] .syftjob-empty::before {
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                }
                .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-empty h3,
                body[data-jp-theme-light="false"] .syftjob-empty h3 {
                    color: white;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                }
                .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-empty p,
                body[data-jp-theme-light="false"] .syftjob-empty p {
                    color: rgba(255,255,255,0.95);
                    opacity: 0.95;
                }
            </style>
            <div class="syftjob-empty">
                <span class="syftjob-empty-icon">📭</span>
                <h3>No jobs found</h3>
                <p>Submit jobs to see them here</p>
            </div>
            """
        
        # Sort jobs by status priority (inbox, approved, done) then by name
        status_priority = {"inbox": 1, "approved": 2, "done": 3}
        sorted_jobs = sorted(self._jobs, key=lambda j: (status_priority.get(j.status, 4), j.name.lower()))
        
        # Status styling for light and dark themes
        status_styles = {
            "inbox": {
                "emoji": "📥", 
                "light": {"color": "#6976ae", "bg": "#e8f2ff"},
                "dark": {"color": "#96d195", "bg": "#52a8c5"}
            },
            "approved": {
                "emoji": "✅", 
                "light": {"color": "#53bea9", "bg": "#e6f9f4"},
                "dark": {"color": "#53bea9", "bg": "#2a5d52"}
            }, 
            "done": {
                "emoji": "🎉", 
                "light": {"color": "#937098", "bg": "#f3e5f5"},
                "dark": {"color": "#f2d98c", "bg": "#cc677b"}
            }
        }
        
        # Build HTML with enhanced visual appeal
        html = f"""
        <style>
            @keyframes syftjob-fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            @keyframes syftjob-statusPulse {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
            }}
            
            .syftjob-container {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 20px 0;
                animation: syftjob-fadeIn 0.6s ease-out;
                border-radius: 16px;
                overflow: auto;
                max-width: 100%;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            
            .syftjob-header {{
                background: linear-gradient(135deg, #f8c073 0%, #f79763 25%, #cc677b 50%, #937098 75%, #6976ae 100%);
                color: white;
                padding: 24px;
                position: relative;
                overflow: hidden;
            }}
            
            .syftjob-header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                animation: syftjob-shine 4s infinite;
            }}
            
            @keyframes syftjob-shine {{
                0% {{ left: -100%; }}
                100% {{ left: 100%; }}
            }}
            
            .syftjob-header h3 {{ 
                margin: 0 0 8px 0; 
                font-size: 22px; 
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                position: relative;
                z-index: 1;
            }}
            .syftjob-header p {{ 
                margin: 0; 
                opacity: 0.9; 
                font-size: 16px; 
                font-weight: 500;
                position: relative;
                z-index: 1;
            }}
            
            .syftjob-table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                table-layout: auto;
                overflow-wrap: break-word;
            }}
            
            .syftjob-thead {{
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            }}
            .syftjob-th {{
                padding: 18px 16px;
                text-align: left;
                font-weight: 700;
                color: #495057;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-right: 1px solid rgba(0,0,0,0.06);
                position: relative;
            }}
            .syftjob-th:last-child {{ border-right: none; }}
            .syftjob-th::after {{
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }}
            
            .syftjob-row-even {{ 
                background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%); 
            }}
            .syftjob-row-odd {{ 
                background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f4 100%); 
            }}
            .syftjob-row {{ 
                border-bottom: 1px solid rgba(0,0,0,0.06);
                transition: all 0.3s ease;
            }}
            .syftjob-row:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                z-index: 10;
                position: relative;
            }}
            
            .syftjob-td {{
                padding: 16px;
                border-right: 1px solid rgba(0,0,0,0.06);
                transition: all 0.2s ease;
            }}
            .syftjob-td:last-child {{ border-right: none; }}
            
            .syftjob-index {{
                background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
                padding: 8px 12px;
                border-radius: 8px;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 13px;
                font-weight: 700;
                color: #495057;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid rgba(0,0,0,0.1);
            }}
            
            .syftjob-job-name {{ 
                font-weight: 600; 
                font-size: 15px;
                color: #2d3748;
            }}
            
            .syftjob-status-inbox {{
                background: linear-gradient(135deg, #6976ae 0%, #52a8c5 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 12px rgba(105, 118, 174, 0.3);
                transition: all 0.3s ease;
            }}
            .syftjob-status-inbox:hover {{
                animation: syftjob-statusPulse 1s infinite;
            }}
            
            .syftjob-status-approved {{
                background: linear-gradient(135deg, #53bea9 0%, #96d195 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 12px rgba(83, 190, 169, 0.3);
                transition: all 0.3s ease;
            }}
            .syftjob-status-approved:hover {{
                animation: syftjob-statusPulse 1s infinite;
            }}
            
            .syftjob-status-done {{
                background: linear-gradient(135deg, #937098 0%, #cc677b 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 12px rgba(147, 112, 152, 0.3);
                transition: all 0.3s ease;
            }}
            .syftjob-status-done:hover {{
                animation: syftjob-statusPulse 1s infinite;
            }}
            
            .syftjob-submitted {{ 
                color: #718096; 
                font-size: 14px; 
                font-style: italic;
            }}
            
            .syftjob-footer {{
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-top: 3px solid transparent;
                background-clip: padding-box;
                position: relative;
            }}
            
            .syftjob-footer::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
            }}
            
            .syftjob-summary {{ 
                display: flex; 
                gap: 20px; 
                align-items: center; 
            }}
            
            .syftjob-summary-item {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 15px;
                font-weight: 600;
                color: #4a5568;
                padding: 6px 12px;
                background: rgba(255,255,255,0.8);
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .syftjob-hint {{
                font-size: 13px;
                color: #718096;
                text-align: right;
                line-height: 1.5;
            }}
            
            .syftjob-code {{
                background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
                padding: 4px 8px;
                border-radius: 6px;
                font-family: 'SF Mono', Monaco, monospace;
                font-weight: 600;
                border: 1px solid rgba(0,0,0,0.1);
            }}
            
            /* Dark theme styles */
            @media (prefers-color-scheme: dark) {{
                .syftjob-container {{
                    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
                }}
                
                .syftjob-header {{
                    background: linear-gradient(135deg, #52a8c5 0%, #6976ae 25%, #937098 50%, #cc677b 75%, #f79763 100%);
                }}
                
                .syftjob-header::before {{
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                }}
                
                .syftjob-table {{ 
                    background: #1a202c; 
                }}
                
                .syftjob-thead {{ 
                    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%); 
                }}
                .syftjob-th {{ 
                    color: #e2e8f0; 
                    border-right-color: rgba(255,255,255,0.1); 
                }}
                .syftjob-th::after {{
                    background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
                }}
                
                .syftjob-row-even {{ 
                    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); 
                }}
                .syftjob-row-odd {{ 
                    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%); 
                }}
                .syftjob-row {{ 
                    border-bottom-color: rgba(255,255,255,0.1); 
                }}
                .syftjob-row:hover {{
                    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                }}
                
                .syftjob-td {{ 
                    border-right-color: rgba(255,255,255,0.1); 
                }}
                
                .syftjob-index {{ 
                    background: linear-gradient(135deg, #4a5568 0%, #718096 100%);
                    color: #e2e8f0;
                    border-color: rgba(255,255,255,0.2);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                .syftjob-job-name {{ color: #e2e8f0; }}
                .syftjob-submitted {{ color: #a0aec0; }}
                
                .syftjob-status-inbox {{ 
                    background: linear-gradient(135deg, #96d195 0%, #f2d98c 100%);
                    color: white;
                    box-shadow: 0 4px 12px rgba(150, 209, 149, 0.4);
                }}
                .syftjob-status-approved {{ 
                    background: linear-gradient(135deg, #53bea9 0%, #52a8c5 100%);
                    color: white;
                    box-shadow: 0 4px 12px rgba(83, 190, 169, 0.4);
                }}
                .syftjob-status-done {{ 
                    background: linear-gradient(135deg, #f2d98c 0%, #f79763 100%);
                    color: #2d3748;
                    box-shadow: 0 4px 12px rgba(242, 217, 140, 0.4);
                }}
                
                .syftjob-footer {{ 
                    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
                }}
                .syftjob-footer::before {{
                    background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
                }}
                
                .syftjob-summary-item {{
                    background: rgba(45, 55, 72, 0.8);
                    color: #e2e8f0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                
                .syftjob-hint {{ color: #a0aec0; }}
                .syftjob-code {{ 
                    background: linear-gradient(135deg, #4a5568 0%, #718096 100%);
                    color: #e2e8f0;
                    border-color: rgba(255,255,255,0.2);
                }}
            }}
            
            /* Jupyter-specific dark theme detection */
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-header,
            body[data-jp-theme-light="false"] .syftjob-header {{
                background: linear-gradient(135deg, #52a8c5 0%, #6976ae 25%, #937098 50%, #cc677b 75%, #f79763 100%);
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-table,
            body[data-jp-theme-light="false"] .syftjob-table {{ 
                box-shadow: 0 2px 8px rgba(0,0,0,0.3); 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-thead,
            body[data-jp-theme-light="false"] .syftjob-thead {{ 
                background: #2d3748; border-bottom-color: #4a5568; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-th,
            body[data-jp-theme-light="false"] .syftjob-th {{ 
                color: #e2e8f0; border-right-color: #4a5568; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-row-even,
            body[data-jp-theme-light="false"] .syftjob-row-even {{ 
                background: #1a202c; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-row-odd,
            body[data-jp-theme-light="false"] .syftjob-row-odd {{ 
                background: #2d3748; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-row,
            body[data-jp-theme-light="false"] .syftjob-row {{ 
                border-bottom-color: #4a5568; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-td,
            body[data-jp-theme-light="false"] .syftjob-td {{ 
                border-right-color: #4a5568; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-index,
            body[data-jp-theme-light="false"] .syftjob-index {{ 
                background: #4a5568; color: #e2e8f0; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-job-name,
            body[data-jp-theme-light="false"] .syftjob-job-name {{ 
                color: #e2e8f0; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-submitted,
            body[data-jp-theme-light="false"] .syftjob-submitted {{ 
                color: #a0aec0; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-status-inbox,
            body[data-jp-theme-light="false"] .syftjob-status-inbox {{ 
                background: linear-gradient(135deg, #96d195 0%, #f2d98c 100%);
                color: white;
                box-shadow: 0 4px 12px rgba(150, 209, 149, 0.4);
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-status-approved,
            body[data-jp-theme-light="false"] .syftjob-status-approved {{ 
                background: linear-gradient(135deg, #53bea9 0%, #52a8c5 100%);
                color: white;
                box-shadow: 0 4px 12px rgba(83, 190, 169, 0.4);
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-status-done,
            body[data-jp-theme-light="false"] .syftjob-status-done {{ 
                background: linear-gradient(135deg, #f2d98c 0%, #f79763 100%);
                color: #2d3748;
                box-shadow: 0 4px 12px rgba(242, 217, 140, 0.4);
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-footer,
            body[data-jp-theme-light="false"] .syftjob-footer {{ 
                background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%); 
                border-top-color: rgba(147,112,152,0.3);
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-hint,
            body[data-jp-theme-light="false"] .syftjob-hint {{ 
                color: #a0aec0; 
            }}
            
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-code,
            body[data-jp-theme-light="false"] .syftjob-code {{ 
                background: #4a5568; color: #e2e8f0; 
            }}
        </style>
        
        <div class="syftjob-container">
            <div class="syftjob-header">
                <h3>📊 Jobs for {self._root_email}</h3>
                <p>Total: {len(self._jobs)} jobs</p>
            </div>
            <table class="syftjob-table">
                <thead class="syftjob-thead">
                    <tr>
                        <th class="syftjob-th">Index</th>
                        <th class="syftjob-th">Job Name</th>
                        <th class="syftjob-th">Status</th>
                        <th class="syftjob-th">Submitted By</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add job rows
        for i, job in enumerate(sorted_jobs):
            style_info = status_styles.get(job.status, {"emoji": "❓"})
            row_class = "syftjob-row-even" if i % 2 == 0 else "syftjob-row-odd"
            
            html += f"""
                    <tr class="{row_class} syftjob-row">
                        <td class="syftjob-td">
                            <span class="syftjob-index">[{i}]</span>
                        </td>
                        <td class="syftjob-td syftjob-job-name">
                            {job.name}
                        </td>
                        <td class="syftjob-td">
                            <span class="syftjob-status-{job.status}">
                                {style_info['emoji']} {job.status.upper()}
                            </span>
                        </td>
                        <td class="syftjob-td syftjob-submitted">
                            {job.submitted_by}
                        </td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        """
        
        # Add status summary
        status_counts = {}
        for job in self._jobs:
            status_counts[job.status] = status_counts.get(job.status, 0) + 1
        
        html += """
            <div class="syftjob-footer">
                <div class="syftjob-summary">
        """
        
        for status, count in status_counts.items():
            style_info = status_styles.get(status, {"emoji": "❓"})
            html += f"""
                    <span class="syftjob-summary-item">
                        {style_info['emoji']} {count} {status}
                    </span>
            """
        
        html += """
                </div>
                <div class="syftjob-hint">
                    💡 Use <code class="syftjob-code">jobs[0].accept_by_depositing_result('file.txt')</code> to complete jobs
                </div>
            </div>
        </div>
        """
        
        return html


class JobClient:
    """Client for submitting jobs to SyftBox."""
    
    def __init__(self, config: SyftJobConfig):
        """Initialize JobClient with configuration."""
        self.config = config
    
    def _ensure_job_directories(self, user_email: str) -> None:
        """Ensure job directory structure exists for a user."""
        job_dir = self.config.get_job_dir(user_email)
        inbox_dir = self.config.get_inbox_dir(user_email)
        approved_dir = self.config.get_approved_dir(user_email)
        done_dir = self.config.get_done_dir(user_email)
        
        # Create directories if they don't exist
        for directory in [job_dir, inbox_dir, approved_dir, done_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def submit_bash_job(self, user: str, job_name: str, script: str) -> Path:
        """
        Submit a bash job for a user.
        
        Args:
            user: Email address of the user to submit job for
            job_name: Name of the job (will be used as directory name)
            script: Bash script content to execute
            
        Returns:
            Path to the created job directory
            
        Raises:
            FileExistsError: If job with same name already exists
            ValueError: If user directory doesn't exist
        """
        # Ensure user directory exists
        user_dir = self.config.get_user_dir(user)
        if not user_dir.exists():
            raise ValueError(f"User directory does not exist: {user_dir}")
        
        # Ensure job directory structure exists
        self._ensure_job_directories(user)
        
        # Create job directory in inbox
        job_dir = self.config.get_inbox_dir(user) / job_name
        
        if job_dir.exists():
            raise FileExistsError(f"Job '{job_name}' already exists in inbox for user '{user}'")
        
        job_dir.mkdir(parents=True)
        
        # Create run.sh file
        run_script_path = job_dir / "run.sh"
        with open(run_script_path, 'w') as f:
            f.write(script)
        
        # Make run.sh executable
        os.chmod(run_script_path, 0o755)
        
        # Create config.yaml file
        config_yaml_path = job_dir / "config.yaml"
        job_config = {
            "name": job_name,
            "submitted_by": self.config.email
        }
        
        with open(config_yaml_path, 'w') as f:
            yaml.dump(job_config, f, default_flow_style=False)
        
        return job_dir
    
    def _get_current_user_jobs(self) -> List[JobInfo]:
        """Get all jobs in the current user's datasite (inbox, approved, done)."""
        jobs = []
        current_user_email = self.config.email
        user_job_dir = self.config.get_job_dir(current_user_email)
        
        if not user_job_dir.exists():
            return jobs
        
        # Check each status directory
        for status_dir_name in ["inbox", "approved", "done"]:
            status_dir = user_job_dir / status_dir_name
            if not status_dir.exists():
                continue
                
            # Scan for job directories
            for job_dir in status_dir.iterdir():
                if not job_dir.is_dir():
                    continue
                    
                config_file = job_dir / "config.yaml"
                if not config_file.exists():
                    continue
                
                try:
                    with open(config_file, 'r') as f:
                        job_config = yaml.safe_load(f)
                    
                    # Include all jobs in current user's datasite
                    jobs.append(JobInfo(
                        name=job_config.get("name", job_dir.name),
                        user=current_user_email,
                        status=status_dir_name,
                        submitted_by=job_config.get("submitted_by", "unknown"),
                        location=job_dir,
                        config=self.config
                    ))
                except Exception as e:
                    # Skip jobs with invalid config files
                    continue
        
        return jobs
    
    @property
    def jobs(self) -> JobsList:
        """
        Get all jobs in the current user's datasite as an indexable list.
        
        Returns a JobsList object that can be:
        - Indexed: jobs[0], jobs[1], etc.
        - Iterated: for job in jobs
        - Displayed: print(jobs) shows a nice table
        
        Each job has an accept_by_depositing_result() method for approval.
        
        Returns:
            JobsList containing all jobs in current user's datasite
        """
        current_jobs = self._get_current_user_jobs()
        return JobsList(current_jobs, self.config.email)


def get_client(config_path: str) -> JobClient:
    """
    Factory function to create a JobClient from config file.
    
    Args:
        config_path: Path to the configuration JSON file
        
    Returns:
        Configured JobClient instance
    """
    config = SyftJobConfig.from_file(config_path)
    return JobClient(config)