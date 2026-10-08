"""Flashy HTML & JavaScript exporter for Strava training results."""
import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from strava_tui.data.models import AggregatedStats, AthleteProfile


class HtmlExporter:
    """Generates a modern, flashy, interactive HTML report with JavaScript charts, confetti, and filtering."""

    @staticmethod
    def export(
        stats: AggregatedStats,
        athlete: AthleteProfile,
        output_path: Optional[Path] = None,
    ) -> Path:
        if output_path is None:
            clean_phrase = "".join(c for c in stats.phrase if c.isalnum() or c in ("-", "_")).strip()
            phrase_part = f"_{clean_phrase}" if clean_phrase else ""
            filename = f"strava_report_{stats.year}{phrase_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            output_path = Path.cwd() / filename

        # Prepare JSON data payloads for JavaScript
        monthly_labels = [m.month_name for m in stats.monthly_breakdown]
        monthly_km = [m.distance_km for m in stats.monthly_breakdown]
        monthly_counts = [m.count for m in stats.monthly_breakdown]

        # Calculate cumulative kilometers
        cumulative_km = []
        running_sum = 0.0
        for km in monthly_km:
            running_sum += km
            cumulative_km.append(round(running_sum, 2))

        sport_labels = [s.sport_type for s in stats.sport_breakdown]
        sport_km = [s.distance_km for s in stats.sport_breakdown]

        activities_data = [
            {
                "id": a.id,
                "name": a.name,
                "sport": a.sport_type,
                "date": a.date_formatted,
                "distance_km": a.distance_km,
                "moving_time": a.moving_time_formatted,
                "elevation": a.total_elevation_gain,
                "pace": a.pace_per_km,
                "avg_speed": a.average_speed_kmh,
                "hr_avg": a.average_heartrate or "-",
                "strava_url": a.strava_url,
            }
            for a in stats.activities
        ]

        # Build self-contained HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Strava Training Report - {stats.year} | {stats.phrase or 'All Activities'}</title>
    <!-- Chart.js and Confetti for flashy visuals -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
    <style>
        :root {{
            --primary: #FC4C02;
            --primary-glow: rgba(252, 76, 2, 0.4);
            --bg-dark: #0a0e17;
            --card-bg: rgba(23, 31, 48, 0.85);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-green: #10B981;
            --accent-blue: #38BDF8;
            --accent-purple: #A855F7;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: radial-gradient(circle at 10% 20%, #171d2b 0%, var(--bg-dark) 90%);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
            min-height: 100vh;
            padding: 30px 20px;
        }}
        .container {{
            max-width: 1300px;
            margin: 0 auto;
        }}
        /* Header Hero */
        .hero {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 30px 40px;
            margin-bottom: 25px;
            backdrop-filter: blur(16px);
            box-shadow: 0 10px 35px rgba(0, 0, 0, 0.4);
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; width: 6px; height: 100%;
            background: linear-gradient(180deg, #FC4C02, #FF8A00);
        }}
        .hero-left h1 {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .strava-badge {{
            background: #FC4C02;
            color: #fff;
            font-size: 0.85rem;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
            font-weight: 700;
        }}
        .hero-left p {{
            color: var(--text-muted);
            margin-top: 6px;
            font-size: 1.05rem;
        }}
        .filter-highlight {{
            color: #FC4C02;
            font-weight: 600;
            background: rgba(252, 76, 2, 0.12);
            padding: 2px 8px;
            border-radius: 6px;
        }}
        .action-bar {{
            display: flex;
            gap: 12px;
        }}
        .btn {{
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-main);
            border: 1px solid var(--card-border);
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            font-size: 0.9rem;
        }}
        .btn:hover {{
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #FC4C02, #FF6A00);
            border: none;
            box-shadow: 0 4px 15px var(--primary-glow);
        }}
        .btn-primary:hover {{
            box-shadow: 0 6px 20px rgba(252, 76, 2, 0.6);
        }}

        /* KPI Metric Cards Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
            position: relative;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
        }}
        .metric-card.hero-metric {{
            background: linear-gradient(135deg, rgba(252, 76, 2, 0.15), rgba(23, 31, 48, 0.95));
            border-color: rgba(252, 76, 2, 0.4);
        }}
        .metric-title {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            color: #fff;
        }}
        .metric-unit {{
            font-size: 1rem;
            color: var(--text-muted);
            font-weight: normal;
            margin-left: 4px;
        }}
        .metric-sub {{
            font-size: 0.85rem;
            color: var(--accent-green);
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        /* Charts Row */
        .charts-row {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
            margin-bottom: 30px;
        }}
        @media (max-width: 950px) {{
            .charts-row {{ grid-template-columns: 1fr; }}
        }}
        .chart-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 24px;
            backdrop-filter: blur(12px);
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }}
        .chart-title {{
            font-size: 1.15rem;
            font-weight: 700;
        }}
        .chart-canvas-wrapper {{
            position: relative;
            height: 290px;
            width: 100%;
        }}

        /* Table Section */
        .table-section {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 26px;
            backdrop-filter: blur(12px);
            margin-bottom: 30px;
        }}
        .table-controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .search-box {{
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px 16px;
            color: #fff;
            font-size: 0.95rem;
            width: 320px;
            outline: none;
            transition: border 0.2s;
        }}
        .search-box:focus {{
            border-color: #FC4C02;
        }}
        .sport-pills {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .pill {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-muted);
        }}
        .pill.active, .pill:hover {{
            background: #FC4C02;
            color: #fff;
            border-color: #FC4C02;
        }}
        .data-table-container {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.92rem;
        }}
        th {{
            padding: 12px 14px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--card-border);
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }}
        th:hover {{
            color: #fff;
        }}
        td {{
            padding: 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            color: #e2e8f0;
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.03);
        }}
        .badge-sport {{
            background: rgba(56, 189, 248, 0.15);
            color: #38BDF8;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .strava-link {{
            color: #FC4C02;
            text-decoration: none;
            font-weight: 600;
        }}
        .strava-link:hover {{
            text-decoration: underline;
        }}
        .footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 40px;
        }}

        @media print {{
            body {{ background: #fff; color: #000; }}
            .btn, .search-box, .sport-pills {{ display: none; }}
            .hero, .metric-card, .chart-card, .table-section {{
                box-shadow: none; border: 1px solid #ddd; background: #fff; color: #000;
            }}
            .metric-value, th, td {{ color: #000; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="hero">
            <div class="hero-left">
                <h1>
                    <span class="strava-badge">Strava</span>
                    <span>Training Analytics</span>
                </h1>
                <p>
                    Athlete: <strong>{athlete.full_name}</strong> |
                    Year: <strong>{stats.year}</strong> |
                    Phrase Filter: {f'<span class="filter-highlight">"{stats.phrase}"</span>' if stats.phrase else '<em>(All Activities)</em>'}
                </p>
            </div>
            <div class="action-bar">
                <button class="btn btn-primary" onclick="triggerConfetti()">🎉 Celebrate</button>
                <button class="btn" onclick="exportCsv()">📥 Download CSV</button>
                <button class="btn" onclick="window.print()">🖨️ Print / PDF</button>
            </div>
        </header>

        <!-- KPI Metrics Grid -->
        <section class="metrics-grid">
            <div class="metric-card hero-metric">
                <div class="metric-title">Combined Distance</div>
                <div class="metric-value" id="kpi-km">0<span class="metric-unit">km</span></div>
                <div class="metric-sub">🚀 Total matching kilometers in {stats.year}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Matching Trainings</div>
                <div class="metric-value" id="kpi-count">0</div>
                <div class="metric-sub">Out of {stats.total_activities_in_year} logged activities</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Total Moving Time</div>
                <div class="metric-value">{stats.total_moving_time_formatted}</div>
                <div class="metric-sub">⏱️ Time spent in motion</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Elevation Gain</div>
                <div class="metric-value" id="kpi-elev">0<span class="metric-unit">m</span></div>
                <div class="metric-sub">⛰️ Combined vertical climbing</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Avg Workout Distance</div>
                <div class="metric-value">{stats.avg_distance_km}<span class="metric-unit">km</span></div>
                <div class="metric-sub">Avg Speed: {stats.avg_speed_kmh} km/h</div>
            </div>
        </section>

        <!-- Visual Interactive Charts -->
        <section class="charts-row">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">Monthly Distance Breakdown ({stats.year})</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">Kilometers per month</div>
                </div>
                <div class="chart-canvas-wrapper">
                    <canvas id="monthlyChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">Sport Type Distribution</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">By distance (km)</div>
                </div>
                <div class="chart-canvas-wrapper">
                    <canvas id="sportChart"></canvas>
                </div>
            </div>
        </section>

        <!-- Cumulative Progress Chart -->
        <section class="chart-card" style="margin-bottom: 30px;">
            <div class="chart-header">
                <div class="chart-title">📈 Cumulative Kilometers Growth Curve</div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">Year-to-date milestone progress</div>
            </div>
            <div class="chart-canvas-wrapper" style="height: 250px;">
                <canvas id="cumulativeChart"></canvas>
            </div>
        </section>

        <!-- Activities Data Table -->
        <section class="table-section">
            <div class="table-controls">
                <input type="text" id="tableSearch" class="search-box" placeholder="🔍 Search matching trainings..." oninput="filterTable()">
                <div class="sport-pills" id="sportFilters">
                    <div class="pill active" onclick="setSportFilter('ALL')">All Sports ({stats.matching_count})</div>
                </div>
            </div>
            <div class="data-table-container">
                <table id="activitiesTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)">Date ↕</th>
                            <th onclick="sortTable(1)">Activity Name ↕</th>
                            <th onclick="sortTable(2)">Sport ↕</th>
                            <th onclick="sortTable(3, true)">Distance (km) ↕</th>
                            <th onclick="sortTable(4)">Time ↕</th>
                            <th onclick="sortTable(5, true)">Elevation (m) ↕</th>
                            <th onclick="sortTable(6)">Pace / Speed ↕</th>
                            <th>Strava</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <!-- Populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </section>

        <footer class="footer">
            Generated with <strong>Strava TUI Analytics</strong> • {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </footer>
    </div>

    <!-- Data Payloads & Interactive Application Script -->
    <script>
        const statsData = {{
            totalKm: {stats.total_distance_km},
            totalCount: {stats.matching_count},
            totalElev: {stats.total_elevation_gain_m},
            monthlyLabels: {json.dumps(monthly_labels)},
            monthlyKm: {json.dumps(monthly_km)},
            cumulativeKm: {json.dumps(cumulative_km)},
            sportLabels: {json.dumps(sport_labels)},
            sportKm: {json.dumps(sport_km)},
            activities: {json.dumps(activities_data)}
        }};

        // 1. Confetti Animation
        function triggerConfetti() {{
            if (typeof confetti === 'function') {{
                confetti({{
                    particleCount: 100,
                    spread: 70,
                    origin: {{ y: 0.6 }},
                    colors: ['#FC4C02', '#FF8A00', '#10B981', '#38BDF8', '#ffffff']
                }});
            }}
        }}

        // 2. Animated Counter function
        function animateCounter(elementId, targetValue, duration = 1200, unit = '') {{
            const el = document.getElementById(elementId);
            if (!el) return;
            const startTime = performance.now();
            const startVal = 0;
            function update(time) {{
                const elapsed = time - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out quad
                const ease = 1 - (1 - progress) * (1 - progress);
                const current = (startVal + (targetValue - startVal) * ease);
                const formatted = Number.isInteger(targetValue) ? Math.round(current) : current.toFixed(1);
                el.innerHTML = formatted + (unit ? `<span class="metric-unit">${{unit}}</span>` : '');
                if (progress < 1) {{
                    requestAnimationFrame(update);
                }}
            }}
            requestAnimationFrame(update);
        }}

        // 3. Render Charts using Chart.js
        function renderCharts() {{
            if (typeof Chart === 'undefined') return;

            // Monthly Bar Chart
            const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
            new Chart(monthlyCtx, {{
                type: 'bar',
                data: {{
                    labels: statsData.monthlyLabels,
                    datasets: [{{
                        label: 'Kilometers (km)',
                        data: statsData.monthlyKm,
                        backgroundColor: 'rgba(252, 76, 2, 0.75)',
                        borderColor: '#FC4C02',
                        borderWidth: 1.5,
                        borderRadius: 6,
                        hoverBackgroundColor: '#FC4C02'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            backgroundColor: '#1e293b',
                            titleColor: '#f8fafc',
                            bodyColor: '#FC4C02',
                            borderColor: '#334155',
                            borderWidth: 1,
                            padding: 10,
                            callbacks: {{
                                label: (ctx) => `${{ctx.parsed.y}} km`
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ grid: {{ display: false }}, ticks: {{ color: '#94a3b8' }} }},
                        y: {{ grid: {{ color: 'rgba(255,255,255,0.06)' }}, ticks: {{ color: '#94a3b8' }} }}
                    }}
                }}
            }});

            // Sport Doughnut Chart
            const sportCtx = document.getElementById('sportChart').getContext('2d');
            new Chart(sportCtx, {{
                type: 'doughnut',
                data: {{
                    labels: statsData.sportLabels,
                    datasets: [{{
                        data: statsData.sportKm,
                        backgroundColor: [
                            '#FC4C02', '#38BDF8', '#10B981', '#A855F7', '#F59E0B', '#EC4899'
                        ],
                        borderWidth: 0,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                            labels: {{ color: '#94a3b8', font: {{ size: 11 }} }}
                        }}
                    }},
                    cutout: '65%'
                }}
            }});

            // Cumulative Area Chart
            const cumulativeCtx = document.getElementById('cumulativeChart').getContext('2d');
            new Chart(cumulativeCtx, {{
                type: 'line',
                data: {{
                    labels: statsData.monthlyLabels,
                    datasets: [{{
                        label: 'Cumulative km',
                        data: statsData.cumulativeKm,
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#10B981',
                        pointRadius: 4,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        x: {{ grid: {{ display: false }}, ticks: {{ color: '#94a3b8' }} }},
                        y: {{ grid: {{ color: 'rgba(255,255,255,0.06)' }}, ticks: {{ color: '#94a3b8' }} }}
                    }}
                }}
            }});
        }}

        // 4. Populate and Filter Table
        let currentSportFilter = 'ALL';
        let sortDirection = 1;

        function populateSportPills() {{
            const container = document.getElementById('sportFilters');
            const sports = [...new Set(statsData.activities.map(a => a.sport))];
            sports.forEach(sport => {{
                const count = statsData.activities.filter(a => a.sport === sport).length;
                const pill = document.createElement('div');
                pill.className = 'pill';
                pill.innerText = `${{sport}} (${{count}})`;
                pill.onclick = () => setSportFilter(sport, pill);
                container.appendChild(pill);
            }});
        }}

        function setSportFilter(sport, el) {{
            currentSportFilter = sport;
            document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
            if (el) {{
                el.classList.add('active');
            }} else {{
                document.querySelector('.pill').classList.add('active');
            }}
            filterTable();
        }}

        function filterTable() {{
            const search = document.getElementById('tableSearch').value.toLowerCase();
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            const filtered = statsData.activities.filter(a => {{
                const matchSport = currentSportFilter === 'ALL' || a.sport === currentSportFilter;
                const matchSearch = a.name.toLowerCase().includes(search) || a.date.toLowerCase().includes(search);
                return matchSport && matchSearch;
            }});

            filtered.forEach(a => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${{a.date}}</td>
                    <td><strong>${{a.name}}</strong></td>
                    <td><span class="badge-sport">${{a.sport}}</span></td>
                    <td><strong>${{a.distance_km}} km</strong></td>
                    <td>${{a.moving_time}}</td>
                    <td>${{a.elevation}} m</td>
                    <td>${{a.sport.toLowerCase().includes('run') ? a.pace : a.avg_speed + ' km/h'}}</td>
                    <td><a href="${{a.strava_url}}" target="_blank" class="strava-link">View ↗</a></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function sortTable(columnIndex, isNumber = false) {{
            sortDirection *= -1;
            statsData.activities.sort((a, b) => {{
                let valA, valB;
                switch (columnIndex) {{
                    case 0: valA = a.date; valB = b.date; break;
                    case 1: valA = a.name; valB = b.name; break;
                    case 2: valA = a.sport; valB = b.sport; break;
                    case 3: valA = a.distance_km; valB = b.distance_km; break;
                    case 4: valA = a.moving_time; valB = b.moving_time; break;
                    case 5: valA = a.elevation; valB = b.elevation; break;
                    case 6: valA = a.avg_speed; valB = b.avg_speed; break;
                    default: return 0;
                }}
                if (isNumber) return (valA - valB) * sortDirection;
                return valA.localeCompare(valB) * sortDirection;
            }});
            filterTable();
        }}

        // 5. CSV Export directly from browser
        function exportCsv() {{
            const headers = ["ID", "Name", "Sport", "Date", "Distance (km)", "Moving Time", "Elevation (m)", "Pace", "Avg Speed (km/h)", "Strava URL"];
            const rows = statsData.activities.map(a => [
                `"${{a.id}}"`,
                `"${{a.name.replace(/"/g, '""')}}"`,
                `"${{a.sport}}"`,
                `"${{a.date}}"`,
                a.distance_km,
                `"${{a.moving_time}}"`,
                a.elevation,
                `"${{a.pace}}"`,
                a.avg_speed,
                `"${{a.strava_url}}"`
            ]);
            const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `strava_{stats.year}_trainings.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}

        // Initialize on page load
        window.addEventListener('DOMContentLoaded', () => {{
            animateCounter('kpi-km', statsData.totalKm, 1400, 'km');
            animateCounter('kpi-count', statsData.totalCount, 1000);
            animateCounter('kpi-elev', statsData.totalElev, 1200, 'm');
            renderCharts();
            populateSportPills();
            filterTable();
            setTimeout(triggerConfetti, 350);
        }});
    </script>
</body>
</html>
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
