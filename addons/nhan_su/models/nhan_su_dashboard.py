# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class NhanSuDashboard(models.Model):
    _name = 'nhan_su.dashboard'
    _description = 'Bảng điều khiển Nhân sự'

    name = fields.Char(default="Tổng quan Nhân sự")
    dashboard_html = fields.Html(compute='_compute_dashboard_html', sanitize=False)

    @api.model
    def action_get_dashboard(self):
        record = self.search([], limit=1)
        if not record:
            record = self.create({'name': 'Tổng quan Nhân sự'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tổng quan Nhân sự',
            'res_model': 'nhan_su.dashboard',
            'view_mode': 'form',
            'res_id': record.id,
            'target': 'current',
            'flags': {'initial_mode': 'view'},
        }

    def _compute_dashboard_html(self):
        for rec in self:
            # Metrics
            total_employees = self.env['nhan_vien'].search_count([])
            total_departments = self.env['don_vi'].search_count([])
            total_jobs = self.env['chuc_vu'].search_count([])
            
            # Count managers (distinct employees who are marked as leader or have manager titles)
            # Or we can count active contracts/work history records
            total_contracts = self.env['lich_su_cong_tac'].search_count([('dang_hieu_luc', '=', True)])

            # 1. Donut Chart - Employees per Department
            departments = self.env['don_vi'].search([])
            dept_counts = []
            total_dept_mapped = 0
            for dept in departments:
                count = self.env['nhan_vien'].search_count([('don_vi_hien_tai_id', '=', dept.id)])
                if count > 0:
                    dept_counts.append((dept.ten_don_vi or "Chưa rõ", count))
                    total_dept_mapped += count
            
            # Handle employees with no department
            no_dept_count = self.env['nhan_vien'].search_count([('don_vi_hien_tai_id', '=', False)])
            if no_dept_count > 0:
                dept_counts.append(("Chưa có phòng ban", no_dept_count))
                total_dept_mapped += no_dept_count

            colors_pool = ['#3498db', '#2ecc71', '#9b59b6', '#e67e22', '#1abc9c', '#e74c3c', '#f1c40f', '#34495e', '#16a085', '#27ae60']
            
            svg_donut = ""
            legend_donut = ""
            if total_employees > 0:
                circumference = 376.99
                offset = 0
                for i, (name, count) in enumerate(dept_counts):
                    color = colors_pool[i % len(colors_pool)]
                    percentage = (count / total_employees) * 100
                    dash = (percentage / 100) * circumference
                    svg_donut += f"""
                    <circle cx="120" cy="120" r="60" fill="transparent" 
                            stroke="{color}" stroke-width="25" 
                            stroke-dasharray="{dash} {circumference}" 
                            stroke-dashoffset="{-offset}">
                        <title>{name}: {count} nhân sự ({percentage:.1f}%)</title>
                    </circle>
                    """
                    offset += dash
                    
                    legend_donut += f"""
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 11px; margin-bottom: 4px;">
                        <span style="display: inline-block; width: 10px; height: 10px; background-color: {color}; border-radius: 2px;"></span>
                        <span style="color: #4a5568;"><b>{name}</b>: {count} ({percentage:.1f}%)</span>
                    </div>
                    """
            else:
                svg_donut = '<circle cx="120" cy="120" r="60" fill="transparent" stroke="#e0e0e0" stroke-width="25"/>'
                legend_donut = '<div style="color: #95a5a6; font-size: 12px;">Không có dữ liệu</div>'

            # 2. Line Chart - Hiring Trend (Latest 5 years/months or employees)
            # We can count hiring trend by year of ngay_vao_lam
            # Let's count employees hired by year
            years = [2022, 2023, 2024, 2025, 2026]
            hired_counts = []
            for y in years:
                start_date = f"{y}-01-01"
                end_date = f"{y}-12-31"
                count = self.env['nhan_vien'].search_count([('ngay_vao_lam', '>=', start_date), ('ngay_vao_lam', '<=', end_date)])
                hired_counts.append(count)
            
            max_hired = max(hired_counts) if max(hired_counts) > 0 else 1
            svg_line = ""
            points = []
            for i, val in enumerate(hired_counts):
                x = 50 + i * 75
                y = 150 - (val / max_hired) * 100
                points.append((x, y))
            
            points_str = " ".join(f"{x},{y}" for x, y in points)
            
            # Grid
            svg_line += '<line x1="40" y1="150" x2="380" y2="150" stroke="#e2e8f0" stroke-width="1"/>'
            svg_line += '<line x1="40" y1="50" x2="380" y2="50" stroke="#f7fafc" stroke-width="1"/>'
            
            # Area and Line
            area_points = f"50,150 {points_str} {50 + (len(years)-1)*75},150"
            svg_line += f'<polygon points="{area_points}" fill="url(#purple-grad)" opacity="0.25"/>'
            svg_line += f'<polyline points="{points_str}" fill="none" stroke="#9b59b6" stroke-width="3"/>'
            
            for i, (x, y) in enumerate(points):
                svg_line += f"""
                <circle cx="{x}" cy="{y}" r="5" fill="#9b59b6" stroke="white" stroke-width="2"/>
                <text x="{x}" y="{y - 10}" font-size="9" font-weight="bold" text-anchor="middle" fill="#2d3748">{hired_counts[i]}</text>
                <text x="{x}" y="165" font-size="9" text-anchor="middle" fill="#718096">{years[i]}</text>
                """

            # 3. Bar Chart - Employees by Job Title
            jobs = self.env['chuc_vu'].search([], limit=5)
            job_counts = []
            max_job_count = 1
            for job in jobs:
                count = self.env['nhan_vien'].search_count([('chuc_vu_hien_tai_id', '=', job.id)])
                job_counts.append((job.ten_chuc_vu or "Khác", count))
                if count > max_job_count:
                    max_job_count = count
            
            svg_bar = ""
            if job_counts:
                for i, (name, count) in enumerate(job_counts):
                    x = 40 + i * 70
                    bar_height = (count / max_job_count) * 120
                    y = 150 - bar_height
                    svg_bar += f"""
                    <rect x="{x}" y="{y}" width="35" height="{bar_height}" fill="#2ecc71" rx="4">
                        <title>{name}: {count} nhân sự</title>
                    </rect>
                    <text x="{x + 17}" y="165" font-size="8" text-anchor="middle" fill="#718096">{name[:8]}</text>
                    <text x="{x + 17}" y="{y - 5}" font-size="10" font-weight="bold" text-anchor="middle" fill="#2d3748">{count}</text>
                    """
            else:
                svg_bar = '<text x="200" y="100" text-anchor="middle" fill="#bdc3c7">Không có dữ liệu</text>'

            # 4. Latest Hired Employees Table Rows
            latest_employees = self.env['nhan_vien'].search([], order='ngay_vao_lam desc', limit=4)
            table_rows = ""
            for emp in latest_employees:
                ngay_vao_str = emp.ngay_vao_lam.strftime('%d/%m/%Y') if emp.ngay_vao_lam else '-'
                table_rows += f"""
                <tr style="border-bottom: 1px solid #edf2f7;">
                    <td style="padding: 10px; font-weight: bold; color: #2d3748;">{emp.ho_va_ten}</td>
                    <td style="padding: 10px; color: #4a5568;">{emp.don_vi_hien_tai_id.ten_don_vi or '-'}</td>
                    <td style="padding: 10px; color: #4a5568;">
                        <span style="padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; background: #ebf5fb; color: #2e86c1;">
                            {emp.chuc_vu_hien_tai_id.ten_chuc_vu or 'Nhân viên'}
                        </span>
                    </td>
                    <td style="padding: 10px; color: #718096;">{ngay_vao_str}</td>
                </tr>
                """
            
            if not table_rows:
                table_rows = '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #a0aec0;">Không có nhân viên</td></tr>'

            # Full HTML Dashboard Layout
            rec.dashboard_html = f"""
            <div style="background-color: #f7fafc; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; min-height: 100vh;">
                <!-- Header Title Bar -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: white; padding: 15px 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                    <h2 style="margin: 0; color: #2d3748; font-size: 18px; font-weight: bold; display: flex; align-items: center; gap: 10px;">
                        <span style="background: #9b59b6; width: 6px; height: 20px; display: inline-block; border-radius: 2px;"></span>
                        TỔNG QUAN NHÂN SỰ (QLNS DASHBOARD)
                    </h2>
                    <span style="font-size: 12px; color: #718096;">Báo cáo thời gian thực</span>
                </div>

                <!-- Top Row Cards -->
                <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01); border-left: 5px solid #3498db;">
                        <div style="font-size: 11px; color: #718096; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Tổng Nhân Viên</div>
                        <div style="font-size: 28px; font-weight: bold; color: #2d3748; margin-top: 5px;">{total_employees}</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01); border-left: 5px solid #2ecc71;">
                        <div style="font-size: 11px; color: #718096; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Số Phòng Ban</div>
                        <div style="font-size: 28px; font-weight: bold; color: #2d3748; margin-top: 5px;">{total_departments}</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01); border-left: 5px solid #e67e22;">
                        <div style="font-size: 11px; color: #718096; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Số Chức Vụ</div>
                        <div style="font-size: 28px; font-weight: bold; color: #2d3748; margin-top: 5px;">{total_jobs}</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01); border-left: 5px solid #9b59b6;">
                        <div style="font-size: 11px; color: #718096; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Hợp Đồng Đang Có Hiệu Lực</div>
                        <div style="font-size: 28px; font-weight: bold; color: #2d3748; margin-top: 5px;">{total_contracts}</div>
                    </div>
                </div>

                <!-- Middle Row Charts -->
                <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                    <!-- Donut Chart -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                        <div style="font-size: 13px; font-weight: bold; color: #2d3748; margin-bottom: 15px; border-bottom: 1px solid #edf2f7; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Phân Bổ Nhân Sự Theo Phòng Ban</div>
                        <div style="display: flex; align-items: center; justify-content: space-around; flex-wrap: wrap; gap: 15px;">
                            <svg width="240" height="240">
                                {svg_donut}
                            </svg>
                            <div style="display: flex; flex-direction: column; gap: 4px; max-height: 200px; overflow-y: auto; padding-right: 5px;">
                                {legend_donut}
                            </div>
                        </div>
                    </div>

                    <!-- Line Chart -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                        <div style="font-size: 13px; font-weight: bold; color: #2d3748; margin-bottom: 15px; border-bottom: 1px solid #edf2f7; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Biểu Đồ Xu Hướng Tuyển Dụng</div>
                        <svg width="100%" height="200" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid meet">
                            <defs>
                                <linearGradient id="purple-grad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stop-color="#9b59b6" stop-opacity="0.6"/>
                                    <stop offset="100%" stop-color="#9b59b6" stop-opacity="0"/>
                                </linearGradient>
                            </defs>
                            {svg_line}
                        </svg>
                    </div>
                </div>

                <!-- Bottom Row -->
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <!-- Bar Chart -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                        <div style="font-size: 13px; font-weight: bold; color: #2d3748; margin-bottom: 15px; border-bottom: 1px solid #edf2f7; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Nhân Sự Phân Bổ Theo Chức Vụ</div>
                        <svg width="100%" height="200" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid meet">
                            {svg_bar}
                        </svg>
                    </div>

                    <!-- Table -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                        <div style="font-size: 13px; font-weight: bold; color: #2d3748; margin-bottom: 15px; border-bottom: 1px solid #edf2f7; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Nhân Sự Mới Nhận Gần Đây</div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 2px solid #edf2f7; color: #718096; font-weight: bold;">
                                    <th style="padding: 8px;">Tên nhân viên</th>
                                    <th style="padding: 8px;">Phòng ban</th>
                                    <th style="padding: 8px;">Chức vụ</th>
                                    <th style="padding: 8px;">Ngày vào làm</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """
