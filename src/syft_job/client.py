import os
import shutil
from pathlib import Path
from typing import List

import yaml

from .config import SyftJobConfig


class JobInfo:
    """Information about a job with approval capabilities."""

    def __init__(
        self,
        name: str,
        user: str,
        status: str,
        submitted_by: str,
        location: Path,
        config: SyftJobConfig,
    ):
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
        return (
            f"JobInfo(name='{self.name}', user='{self.user}', status='{self.status}')"
        )

    def accept_by_depositing_result(self, path: str) -> Path:
        """
        Accept a job by depositing the result file or folder and moving it to done status.

        Args:
            path: Path to the result file or folder to deposit

        Returns:
            Path to the deposited result file or folder in the outputs directory

        Raises:
            ValueError: If job is not in inbox status
            FileNotFoundError: If the result file or folder doesn't exist
        """
        if self.status != "inbox":
            raise ValueError(
                f"Job '{self.name}' is not in inbox status (current: {self.status})"
            )

        result_path = Path(path)
        if not result_path.exists():
            raise FileNotFoundError(f"Result path not found: {path}")

        # Prepare done directory path
        done_dir = self._config.get_done_dir(self.user) / self.name

        # Ensure the parent done directory exists, but not the job directory itself
        done_dir.parent.mkdir(parents=True, exist_ok=True)

        # Move the job from inbox to done
        shutil.move(str(self.location), str(done_dir))

        # Create outputs directory in the done job
        outputs_dir = done_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)

        # Handle both files and folders
        result_name = result_path.name
        destination = outputs_dir / result_name

        if result_path.is_file():
            # Copy file to outputs directory
            shutil.copy2(str(result_path), str(destination))
        elif result_path.is_dir():
            # Copy entire directory to outputs directory
            shutil.copytree(str(result_path), str(destination))
        else:
            raise ValueError(f"Path is neither a file nor a directory: {path}")

        # Update this object's state
        self.status = "done"
        self.location = done_dir

        return destination

    def _repr_html_(self) -> str:
        """HTML representation for individual job display in Jupyter."""
        # Status styling
        status_styles = {
            "inbox": {"color": "#6976ae", "bg": "#e8f2ff", "emoji": "📥"},
            "approved": {"color": "#53bea9", "bg": "#e6f9f4", "emoji": "✅"},
            "done": {"color": "#937098", "bg": "#f3e5f5", "emoji": "🎉"},
        }

        style_info = status_styles.get(
            self.status, {"color": "#718096", "bg": "#f7fafc", "emoji": "❓"}
        )

        # Read job script if available
        script_content = "No script available"
        try:
            script_file = self.location / "run.sh"
            if script_file.exists():
                with open(script_file, "r") as f:
                    script_content = f.read().strip()
                    # If content is too long, truncate and add ellipsis
                    if len(script_content) > 500:
                        script_content = script_content[:500] + "..."
                    # Escape HTML characters
                    script_content = (
                        script_content.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace('"', "&quot;")
                        .replace("'", "&#x27;")
                    )
        except Exception:
            pass

        # Read job config if available
        submitted_time = "Unknown"
        try:
            config_file = self.location / "config.yaml"
            if config_file.exists():
                from datetime import datetime

                import yaml

                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)
                    submitted_at = config_data.get("submitted_at")

                    if submitted_at:
                        # Parse ISO format timestamp
                        try:
                            dt = datetime.fromisoformat(
                                submitted_at.replace("Z", "+00:00")
                            )
                            submitted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            submitted_time = str(submitted_at)
                    else:
                        # Fallback to file modification time
                        import os

                        mtime = os.path.getmtime(config_file)
                        dt = datetime.fromtimestamp(mtime)
                        submitted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # If no config file, use job directory modification time
                import os

                if self.location.exists():
                    mtime = os.path.getmtime(self.location)
                    dt = datetime.fromtimestamp(mtime)
                    submitted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            submitted_time = "Unknown"

        return f"""
        <style>
            .syftjob-single {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin: 16px 0;
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 600px;
            }}
            .syftjob-single-header {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid #e2e8f0;
            }}
            .syftjob-single-status {{
                background: {style_info['bg']};
                color: {style_info['color']};
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}
            .syftjob-single-name {{
                font-size: 18px;
                font-weight: 600;
                color: #1a202c;
                margin: 0;
                flex: 1;
            }}
            .syftjob-single-details {{
                display: grid;
                gap: 8px;
                font-size: 14px;
                color: #4a5568;
            }}
            .syftjob-single-detail {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .syftjob-single-detail strong {{
                color: #2d3748;
                font-weight: 600;
                min-width: 100px;
            }}
            .syftjob-single-script {{
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 12px;
                font-family: 'Monaco', 'Menlo', 'SF Mono', monospace;
                font-size: 11px;
                color: #2d3748;
                margin-top: 8px;
                overflow: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
                max-height: 200px;
                line-height: 1.4;
            }}

            /* Dark theme */
            @media (prefers-color-scheme: dark) {{
                .syftjob-single {{
                    background: #1a202c;
                    border-color: #4a5568;
                    color: #e2e8f0;
                }}
                .syftjob-single-header {{
                    border-bottom-color: #4a5568;
                }}
                .syftjob-single-name {{
                    color: #f7fafc;
                }}
                .syftjob-single-details {{
                    color: #cbd5e0;
                }}
                .syftjob-single-detail strong {{
                    color: #e2e8f0;
                }}
                .syftjob-single-script {{
                    background: #2d3748;
                    border-color: #4a5568;
                    color: #e2e8f0;
                }}
            }}

            /* Jupyter dark theme */
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-single,
            body[data-jp-theme-light="false"] .syftjob-single {{
                background: #1a202c;
                border-color: #4a5568;
                color: #e2e8f0;
            }}
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-single-header,
            body[data-jp-theme-light="false"] .syftjob-single-header {{
                border-bottom-color: #4a5568;
            }}
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-single-name,
            body[data-jp-theme-light="false"] .syftjob-single-name {{
                color: #f7fafc;
            }}
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-single-details,
            body[data-jp-theme-light="false"] .syftjob-single-details {{
                color: #cbd5e0;
            }}
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-single-detail strong,
            body[data-jp-theme-light="false"] .syftjob-single-detail strong {{
                color: #e2e8f0;
            }}
            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-single-script,
            body[data-jp-theme-light="false"] .syftjob-single-script {{
                background: #2d3748;
                border-color: #4a5568;
                color: #e2e8f0;
            }}
        </style>
        <div class="syftjob-single">
            <div class="syftjob-single-header">
                <h3 class="syftjob-single-name">{self.name}</h3>
                <span class="syftjob-single-status">
                    {style_info['emoji']} {self.status.upper()}
                </span>
            </div>
            <div class="syftjob-single-details">
                <div class="syftjob-single-detail">
                    <strong>User:</strong>
                    <span>{self.user}</span>
                </div>
                <div class="syftjob-single-detail">
                    <strong>Submitted by:</strong>
                    <span>{self.submitted_by}</span>
                </div>
                <div class="syftjob-single-detail">
                    <strong>Location:</strong>
                    <span>{self.location}</span>
                </div>
                <div class="syftjob-single-detail">
                    <strong>Submitted:</strong>
                    <span>{submitted_time}</span>
                </div>
                <div class="syftjob-single-detail">
                    <strong>Script:</strong>
                    <div class="syftjob-single-script">{script_content}</div>
                </div>
            </div>
        </div>
        """


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
        status_emojis = {"inbox": "📥", "approved": "✅", "done": "🎉"}

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
        sorted_jobs = sorted(
            self._jobs, key=lambda j: (status_priority.get(j.status, 4), j.name.lower())
        )

        # Job rows
        for i, job in enumerate(sorted_jobs):
            emoji = status_emojis.get(job.status, "❓")
            status_display = f"{emoji} {job.status}"
            line = f"[{i:<4}] {job.name:<{name_width}} {status_display:<{status_width}}"
            lines.append(line)

        lines.append("")
        lines.append(f"📈 Total: {len(self._jobs)} jobs")

        # Status summary
        status_counts: dict[str, int] = {}
        for job in self._jobs:
            status_counts[job.status] = status_counts.get(job.status, 0) + 1

        summary_parts = []
        for status, count in status_counts.items():
            emoji = status_emojis.get(status, "❓")
            summary_parts.append(f"{emoji} {count} {status}")

        if summary_parts:
            lines.append("📋 " + " | ".join(summary_parts))

        lines.append("")
        lines.append(
            "💡 Use job_client.jobs[0].accept_by_depositing_result('file_or_folder') to approve jobs"
        )

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"JobsList({len(self._jobs)} jobs)"

    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks with enhanced visual appeal."""
        if not self._jobs:
            return """
            <style>

                .syftjob-empty {
                    padding: 30px 20px;
                    text-align: center;
                    border-radius: 8px;
                    background: linear-gradient(135deg, #f8c073 0%, #f79763 50%, #cc677b 100%);
                    border: 1px solid rgba(248,192,115,0.2);
                    color: white;
                }


                .syftjob-empty h3 {
                    margin: 0 0 12px 0;
                    font-size: 18px;
                    color: white;
                    font-weight: 600;
                }

                .syftjob-empty p {
                    margin: 0;
                    color: rgba(255,255,255,0.9);
                    font-size: 16px;
                    opacity: 0.95;
                }

                .syftjob-empty-icon {
                    font-size: 24px;
                    margin-bottom: 12px;
                    display: block;
                }

                /* Dark theme */
                @media (prefers-color-scheme: dark) {
                    .syftjob-empty {
                        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                        border-color: rgba(74,85,104,0.2);
                    }
                    .syftjob-empty h3 {
                        color: white;
                    }
                    .syftjob-empty p {
                        color: rgba(255,255,255,0.95);
                        opacity: 0.95;
                    }
                }

                /* Jupyter dark theme detection */
                .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-empty,
                body[data-jp-theme-light="false"] .syftjob-empty {
                    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                    border-color: rgba(74,85,104,0.2);
                }
                .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-empty h3,
                body[data-jp-theme-light="false"] .syftjob-empty h3 {
                    color: white;
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
        sorted_jobs = sorted(
            self._jobs, key=lambda j: (status_priority.get(j.status, 4), j.name.lower())
        )

        # Status styling for light and dark themes
        status_styles = {
            "inbox": {
                "emoji": "📥",
                "light": {"color": "#6976ae", "bg": "#e8f2ff"},
                "dark": {"color": "#96d195", "bg": "#52a8c5"},
            },
            "approved": {
                "emoji": "✅",
                "light": {"color": "#53bea9", "bg": "#e6f9f4"},
                "dark": {"color": "#53bea9", "bg": "#2a5d52"},
            },
            "done": {
                "emoji": "🎉",
                "light": {"color": "#937098", "bg": "#f3e5f5"},
                "dark": {"color": "#f2d98c", "bg": "#cc677b"},
            },
        }

        # Build HTML with enhanced visual appeal
        html = f"""
        <style>

            .syftjob-container {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 20px 0;
                border-radius: 8px;
                overflow: auto;
                max-width: 100%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
            }}

            .syftjob-header {{
                background: linear-gradient(135deg, #f8c073 0%, #f79763 25%, #cc677b 50%, #937098 75%, #6976ae 100%);
                color: white;
                padding: 20px;
            }}

            .syftjob-header h3 {{
                margin: 0 0 8px 0;
                font-size: 20px;
                font-weight: 600;
            }}
            .syftjob-header p {{
                margin: 0;
                opacity: 0.9;
                font-size: 14px;
                font-weight: 400;
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
                background: #6976ae;
                color: white;
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}

            .syftjob-status-approved {{
                background: #53bea9;
                color: white;
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}

            .syftjob-status-done {{
                background: #937098;
                color: white;
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 4px;
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
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    border-color: #4a5568;
                }}

                .syftjob-header {{
                    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
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
                    background: linear-gradient(135deg, #4a5568 0%, #718096 100%);
                    color: #e2e8f0;
                    box-shadow: 0 2px 8px rgba(74, 85, 104, 0.3);
                }}
                .syftjob-status-approved {{
                    background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
                    color: #c6f6d5;
                    box-shadow: 0 2px 8px rgba(56, 161, 105, 0.3);
                }}
                .syftjob-status-done {{
                    background: linear-gradient(135deg, #805ad5 0%, #6b46c1 100%);
                    color: #e9d8fd;
                    box-shadow: 0 2px 8px rgba(128, 90, 213, 0.3);
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
                background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
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
                background: linear-gradient(135deg, #4a5568 0%, #718096 100%);
                color: #e2e8f0;
                box-shadow: 0 2px 8px rgba(74, 85, 104, 0.3);
            }}

            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-status-approved,
            body[data-jp-theme-light="false"] .syftjob-status-approved {{
                background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
                color: #c6f6d5;
                box-shadow: 0 2px 8px rgba(56, 161, 105, 0.3);
            }}

            .jp-RenderedHTMLCommon[data-jp-theme-light="false"] .syftjob-status-done,
            body[data-jp-theme-light="false"] .syftjob-status-done {{
                background: linear-gradient(135deg, #805ad5 0%, #6b46c1 100%);
                color: #e9d8fd;
                box-shadow: 0 2px 8px rgba(128, 90, 213, 0.3);
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
        status_counts: dict[str, int] = {}
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
                    💡 Use <code class="syftjob-code">jobs[0].accept_by_depositing_result('file_or_folder')</code> to complete jobs
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
            raise FileExistsError(
                f"Job '{job_name}' already exists in inbox for user '{user}'"
            )

        job_dir.mkdir(parents=True)

        # Create run.sh file
        run_script_path = job_dir / "run.sh"
        with open(run_script_path, "w") as f:
            f.write(script)

        # Make run.sh executable
        os.chmod(run_script_path, 0o755)

        # Create config.yaml file
        config_yaml_path = job_dir / "config.yaml"
        from datetime import datetime, timezone

        job_config = {
            "name": job_name,
            "submitted_by": self.config.email,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(config_yaml_path, "w") as f:
            yaml.dump(job_config, f, default_flow_style=False)

        return job_dir

    def _get_current_user_jobs(self) -> List[JobInfo]:
        """Get all jobs in the current user's datasite (inbox, approved, done)."""
        jobs: list[JobInfo] = []
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
                    with open(config_file, "r") as f:
                        job_config = yaml.safe_load(f)

                    # Include all jobs in current user's datasite
                    jobs.append(
                        JobInfo(
                            name=job_config.get("name", job_dir.name),
                            user=current_user_email,
                            status=status_dir_name,
                            submitted_by=job_config.get("submitted_by", "unknown"),
                            location=job_dir,
                            config=self.config,
                        )
                    )
                except Exception:
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


def get_client(syftbox_folder_path: str) -> JobClient:
    """
    Factory function to create a JobClient from SyftBox folder.

    Args:
        syftbox_folder_path: Path to the SyftBox_{email} folder

    Returns:
        Configured JobClient instance
    """
    config = SyftJobConfig.from_syftbox_folder(syftbox_folder_path)
    return JobClient(config)
