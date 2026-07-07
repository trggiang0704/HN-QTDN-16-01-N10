# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class KhachHangDashboard(models.Model):
    _name = 'khach_hang.dashboard'
    _description = 'Bảng điều khiển Khách hàng'

    name = fields.Char(default="Tổng quan CRM")
    dashboard_html = fields.Html(compute='_compute_dashboard_html', sanitize=False)

    @api.model
    def action_get_dashboard(self):
        record = self.search([], limit=1)
        if not record:
            record = self.create({'name': 'Tổng quan CRM'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tổng quan CRM',
            'res_model': 'khach_hang.dashboard',
            'view_mode': 'form',
            'res_id': record.id,
            'target': 'current',
            'flags': {'initial_mode': 'view'},
        }

    def _compute_dashboard_html(self):
        for rec in self:
            # Metrics
            total_customers = self.env['khach_hang'].search_count([])
            total_leads = self.env['khach_hang'].search_count([('giai_doan', 'in', ['tiep_can', 'ket_noi', 'dam_phan'])])
            total_contracts = self.env['hop_dong'].search_count([('trang_thai', '=', 'dang_thuc_hien')])
            total_revenue = sum(self.env['hop_dong'].search([]).mapped('gia_tri_hop_dong'))

            # 1. Donut Chart
            stages = ['tiep_can', 'ket_noi', 'dam_phan', 'ky_hop_dong', 'thanh_cong', 'that_bai']
            stage_names = {
                'tiep_can': 'Tiếp cận',
                'ket_noi': 'Đã kết nối',
                'dam_phan': 'Đàm phán',
                'ky_hop_dong': 'Ký hợp đồng',
                'thanh_cong': 'Thành công',
                'that_bai': 'Thất bại'
            }
            colors = {
                'tiep_can': '#3498db',
                'ket_noi': '#9b59b6',
                'dam_phan': '#e67e22',
                'ky_hop_dong': '#2ecc71',
                'thanh_cong': '#27ae60',
                'that_bai': '#e74c3c'
            }
            
            stage_counts = {}
            total = 0
            for s in stages:
                count = self.env['khach_hang'].search_count([('giai_doan', '=', s)])
                stage_counts[s] = count
                total += count
            
            svg_donut = ""
            legend_donut = ""
            if total > 0:
                circumference = 376.99
                offset = 0
                for s in stages:
                    count = stage_counts[s]
                    percentage = (count / total) * 100 if total > 0 else 0
                    if count > 0:
                        dash = (percentage / 100) * circumference
                        svg_donut += f"""
                        <circle cx="120" cy="120" r="60" fill="transparent" 
                                stroke="{colors[s]}" stroke-width="25" 
                                stroke-dasharray="{dash} {circumference}" 
                                stroke-dashoffset="{-offset}">
                            <title>{stage_names[s]}: {count} ({percentage:.1f}%)</title>
                        </circle>
                        """
                        offset += dash
                    
                    legend_donut += f"""
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 11px;">
                        <span style="display: inline-block; width: 12px; height: 12px; background-color: {colors[s]}; border-radius: 2px;"></span>
                        <span style="color: #555;"><b>{stage_names[s]}</b>: {count} ({percentage:.1f}%)</span>
                    </div>
                    """
            else:
                svg_donut = '<circle cx="120" cy="120" r="60" fill="transparent" stroke="#e0e0e0" stroke-width="25"/>'
                legend_donut = '<div style="color: #95a5a6; font-size: 12px;">Không có dữ liệu</div>'

            # 2. Line Chart (Recent Contracts)
            last_contracts = self.env['hop_dong'].search([], order='ngay_bat_dau desc', limit=5)
            svg_line = ""
            if last_contracts:
                vals = [c.gia_tri_hop_dong for c in last_contracts][::-1]
                names = [c.ten[:10] + "..." if len(c.ten) > 10 else c.ten for c in last_contracts][::-1]
                max_val = max(vals) if max(vals) > 0 else 1
                
                points = []
                for i, val in enumerate(vals):
                    x = 50 + i * 75
                    y = 150 - (val / max_val) * 100
                    points.append((x, y))
                
                points_str = " ".join(f"{x},{y}" for x, y in points)
                
                # Grid
                svg_line += '<line x1="40" y1="150" x2="380" y2="150" stroke="#e0e0e0" stroke-width="1"/>'
                svg_line += '<line x1="40" y1="50" x2="380" y2="50" stroke="#f5f5f5" stroke-width="1"/>'
                
                # Area and Polyline
                area_points_str = f"50,150 {points_str} {50 + (len(vals)-1)*75},150"
                svg_line += f'<polygon points="{area_points_str}" fill="url(#blue-grad)" opacity="0.35"/>'
                svg_line += f'<polyline points="{points_str}" fill="none" stroke="#3498db" stroke-width="3"/>'
                
                for i, (x, y) in enumerate(points):
                    svg_line += f"""
                    <circle cx="{x}" cy="{y}" r="5" fill="#3498db" stroke="white" stroke-width="2"/>
                    <text x="{x}" y="{y - 10}" font-size="9" font-weight="bold" text-anchor="middle" fill="#2c3e50">{vals[i]:,.0f}</text>
                    <text x="{x}" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">{names[i]}</text>
                    """
            else:
                svg_line = '<text x="200" y="100" text-anchor="middle" fill="#bdc3c7">Không có dữ liệu</text>'

            # 3. Bar Chart (Customer allocation by employee)
            employees = self.env['nhan_vien'].search([], limit=5)
            max_count = 1
            emp_data = []
            for emp in employees:
                count = self.env['khach_hang'].search_count([('nhan_vien_id', '=', emp.id)])
                emp_data.append((emp.ho_va_ten or "Chưa rõ", count))
                if count > max_count:
                    max_count = count
            
            svg_bar = ""
            if emp_data:
                for i, (name, count) in enumerate(emp_data):
                    x = 40 + i * 70
                    bar_height = (count / max_count) * 120
                    y = 150 - bar_height
                    svg_bar += f"""
                    <rect x="{x}" y="{y}" width="35" height="{bar_height}" fill="#f39c12" rx="4">
                        <title>{name}: {count} khách hàng</title>
                    </rect>
                    <text x="{x + 17}" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">{name[:8]}</text>
                    <text x="{x + 17}" y="{y - 5}" font-size="10" font-weight="bold" text-anchor="middle" fill="#2c3e50">{count}</text>
                    """
            else:
                svg_bar = '<text x="200" y="100" text-anchor="middle" fill="#bdc3c7">Không có dữ liệu</text>'

            # 4. Latest Customers Table Rows
            latest_customers = self.env['khach_hang'].search([], order='ngay_nhan_lead desc', limit=4)
            table_rows = ""
            for cust in latest_customers:
                stage_badge_colors = {
                    'tiep_can': 'background: #ebf5fb; color: #2e86c1;',
                    'ket_noi': 'background: #f4ecf7; color: #8e44ad;',
                    'dam_phan': 'background: #fdf2e9; color: #d35400;',
                    'ky_hop_dong': 'background: #e8f8f5; color: #117a65;',
                    'thanh_cong': 'background: #e8f8f5; color: #27ae60;',
                    'that_bai': 'background: #fdedec; color: #c0392b;'
                }
                style_badge = stage_badge_colors.get(cust.giai_doan, 'background: #f4f6f7; color: #7f8c8d;')
                table_rows += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 10px; font-weight: bold; color: #34495e;">{cust.name}</td>
                    <td style="padding: 10px; color: #555;">{cust.phone or '-'}</td>
                    <td style="padding: 10px;">
                        <span style="padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; {style_badge}">
                            {stage_names.get(cust.giai_doan, 'Chưa rõ')}
                        </span>
                    </td>
                    <td style="padding: 10px; color: #7f8c8d;">{cust.nhan_vien_id.ho_va_ten or 'Chưa phân công'}</td>
                </tr>
                """
            
            if not table_rows:
                table_rows = '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #bdc3c7;">Không có dữ liệu</td></tr>'

            # Full HTML Dashboard
            rec.dashboard_html = f"""
            <div style="background-color: #f4f6f9; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; min-height: 100vh;">
                <!-- Top Row Cards -->
                <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid #3498db;">
                        <div style="font-size: 11px; color: #7f8c8d; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Tổng Khách Hàng</div>
                        <div style="font-size: 28px; font-weight: bold; color: #2c3e50; margin-top: 5px;">{total_customers}</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid #e67e22;">
                        <div style="font-size: 11px; color: #7f8c8d; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Khách Hàng Tiềm Năng</div>
                        <div style="font-size: 28px; font-weight: bold; color: #2c3e50; margin-top: 5px;">{total_leads}</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid #2ecc71;">
                        <div style="font-size: 11px; color: #7f8c8d; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Hợp Đồng Đang Thực Hiện</div>
                        <div style="font-size: 28px; font-weight: bold; color: #2c3e50; margin-top: 5px;">{total_contracts}</div>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid #9b59b6;">
                        <div style="font-size: 11px; color: #7f8c8d; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Doanh Thu Đã Ký</div>
                        <div style="font-size: 24px; font-weight: bold; color: #2c3e50; margin-top: 5px;">{total_revenue:,.0f} <span style="font-size: 14px;">đ</span></div>
                    </div>
                </div>

                <!-- Middle Row -->
                <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                    <!-- Donut Chart -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                        <div style="font-size: 13px; font-weight: bold; color: #34495e; margin-bottom: 15px; border-bottom: 1px solid #f2f4f4; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Tỷ Lệ Khách Hàng Theo Giai Đoạn</div>
                        <div style="display: flex; align-items: center; justify-content: space-around; flex-wrap: wrap; gap: 15px;">
                            <svg width="240" height="240">
                                {svg_donut}
                            </svg>
                            <div style="display: flex; flex-direction: column; gap: 8px;">
                                {legend_donut}
                            </div>
                        </div>
                    </div>

                    <!-- Line Chart -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                        <div style="font-size: 13px; font-weight: bold; color: #34495e; margin-bottom: 15px; border-bottom: 1px solid #f2f4f4; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Giá Trị Hợp Đồng Gần Đây</div>
                        <svg width="100%" height="200" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid meet">
                            <defs>
                                <linearGradient id="blue-grad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stop-color="#3498db" stop-opacity="0.6"/>
                                    <stop offset="100%" stop-color="#3498db" stop-opacity="0"/>
                                </linearGradient>
                            </defs>
                            {svg_line}
                        </svg>
                    </div>
                </div>

                <!-- Bottom Row -->
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <!-- Bar Chart -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                        <div style="font-size: 13px; font-weight: bold; color: #34495e; margin-bottom: 15px; border-bottom: 1px solid #f2f4f4; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Phân Bổ Khách Hàng Theo Nhân Sự</div>
                        <svg width="100%" height="200" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid meet">
                            {svg_bar}
                        </svg>
                    </div>

                    <!-- Table -->
                    <div style="flex: 1; min-width: 350px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                        <div style="font-size: 13px; font-weight: bold; color: #34495e; margin-bottom: 15px; border-bottom: 1px solid #f2f4f4; padding-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Khách Hàng Mới Cập Nhật</div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 2px solid #f2f4f4; color: #7f8c8d; font-weight: bold;">
                                    <th style="padding: 8px;">Tên khách hàng</th>
                                    <th style="padding: 8px;">Số điện thoại</th>
                                    <th style="padding: 8px;">Giai đoạn</th>
                                    <th style="padding: 8px;">Người phụ trách</th>
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
