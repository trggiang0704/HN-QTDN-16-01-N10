# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class KhachHang(models.Model):
    _name = 'khach_hang'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Khách Hàng'
    _rec_name = 'name'

    # --- GIỮ NGUYÊN BẢN GỐC ---
    ma_khach_hang = fields.Char(string="Mã khách hàng", required=True, 
                                copy=False, default=lambda self: _('Mới'))
    name = fields.Char(string='Tên khách hàng', required=True, tracking=True)
    loai_khach = fields.Selection([
        ('tiem_nang', 'Từ Lead'),
        ('truc_tiep', 'Tạo trực tiếp')
    ], string="Loại khách hàng", default='truc_tiep')

    lich_su_ids = fields.One2many('lich_su_tuong_tac', 'khach_hang_id', string="Lịch sử tương tác")
    description = fields.Html(string="Ghi chú")
    bao_gia_ids = fields.One2many('bao_gia', 'khach_hang_id', string="Danh sách báo giá")
    tai_lieu_ids = fields.One2many('tai_lieu_phap_ly', 'khach_hang_id', string="Hồ sơ pháp lý")
    
    # 1. TÍCH HỢP LƯU TRỮ HỢP ĐỒNG (Thêm trường liên kết)
    hop_dong_ids = fields.One2many('hop_dong', 'khach_hang_id', string="Hợp đồng đã ký")



    giai_doan = fields.Selection([
        ('tiep_can', 'Tiếp cận'),
        ('ket_noi', 'Đã kết nối'),
        ('dam_phan', 'Đàm phán'),
        ('ky_hop_dong', 'Ký hợp đồng'),
        ('thanh_cong', 'Thành công'),
        ('that_bai', 'Thất bại'),
    ], string='Giai đoạn', default='tiep_can', tracking=True)

    doanh_thu_tiem_nang = fields.Float(string='Doanh thu dự kiến', tracking=True)
    ngay_nhan_lead = fields.Datetime(string="Ngày nhận lead", default=fields.Datetime.now, tracking=True)
    gender = fields.Selection([('nam', 'Nam'), ('nu', 'Nữ'), ('khac', 'Khác')], string='Giới tính', default='nam', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Số điện thoại', tracking=True)
    address = fields.Char(string='Địa chỉ', tracking=True)
    birthday = fields.Date(string='Ngày sinh/Ngày thành lập')
    image = fields.Binary(string="Ảnh/Logo")
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên phụ trách', tracking=True)
    
    # --- UI UPGRADE FIELDS & METHODS ---
    display_dashboard = fields.Html(compute='_compute_display_dashboard', string="Bảng tổng quan")
    hop_dong_count = fields.Integer(compute='_compute_hop_dong_count')

    def _compute_display_dashboard(self):
        for rec in self:
            total_hd = sum(rec.hop_dong_ids.mapped('gia_tri_hop_dong'))
            total_bg = sum(rec.bao_gia_ids.mapped('tong_tien'))
            interactions = len(rec.lich_su_ids)
            rec.display_dashboard = f"""
                <div style="display: flex; gap: 15px; margin-bottom: 20px; font-family: 'Segoe UI', Arial, sans-serif;">
                    <div style="flex: 1; background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="font-size: 11px; text-transform: uppercase; opacity: 0.8; font-weight: bold; letter-spacing: 0.5px;">Tổng giá trị Hợp đồng</div>
                        <div style="font-size: 20px; font-weight: bold; margin-top: 5px;">{total_hd:,.0f} VNĐ</div>
                    </div>
                    <div style="flex: 1; background: linear-gradient(135deg, #2ecc71, #27ae60); color: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="font-size: 11px; text-transform: uppercase; opacity: 0.8; font-weight: bold; letter-spacing: 0.5px;">Tổng giá trị Báo giá</div>
                        <div style="font-size: 20px; font-weight: bold; margin-top: 5px;">{total_bg:,.0f} VNĐ</div>
                    </div>
                    <div style="flex: 1; background: linear-gradient(135deg, #e67e22, #d35400); color: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="font-size: 11px; text-transform: uppercase; opacity: 0.8; font-weight: bold; letter-spacing: 0.5px;">Số lần tương tác</div>
                        <div style="font-size: 20px; font-weight: bold; margin-top: 5px;">{interactions} lần</div>
                    </div>
                </div>
            """

    def _compute_hop_dong_count(self):
        for rec in self:
            rec.hop_dong_count = len(rec.hop_dong_ids)

    def action_view_hop_dong(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hợp đồng của khách hàng',
            'res_model': 'hop_dong',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id},
        }

    @api.model
    def create(self, vals):
        if vals.get('ma_khach_hang', _('Mới')) == _('Mới'):
            vals['ma_khach_hang'] = self.env['ir.sequence'].next_by_code('khach_hang.code') or _('Mới')
        return super(KhachHang, self).create(vals)

    # 3. TÍCH HỢP TẠO HỢP ĐỒNG KHI BẤM NÚT (Sửa hàm này)
    def action_set_contract(self):
        for rec in self:
            rec.giai_doan = 'ky_hop_dong'
            # Tự động tạo bản ghi bên bảng Hợp đồng
            self.env['hop_dong'].create({
                'ten': f"Hợp đồng kinh tế: {rec.name}",
                'khach_hang_id': rec.id,
                'gia_tri_hop_dong': rec.doanh_thu_tiem_nang,
                'ngay_bat_dau': fields.Date.today(),
                'trang_thai': 'dang_thuc_hien',
            })

    def action_set_done(self):
        self.giai_doan = 'thanh_cong'

    def action_set_fail(self):
        self.giai_doan = 'that_bai'

    def action_open_ai_chatbot(self):
        """Mở AI Chatbot với ngữ cảnh khách hàng hiện tại"""
        self.ensure_one()
        return self.env['ai.chatbot.wizard'].action_open_chatbot(
            res_model='khach_hang',
            res_id=self.id
        )
