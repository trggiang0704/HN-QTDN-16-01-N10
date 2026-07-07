# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class QuanLyVanBan(models.Model):
    _name = "quan_ly_van_ban"
    _description = "Quản lý văn bản văn phòng"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'so_hieu'

    so_hieu = fields.Char(string="Số hiệu văn bản", required=True, copy=False, 
                         readonly=True, default=lambda self: 'Mới', tracking=True)
    ten_van_ban = fields.Char(string="Trích yếu nội dung", required=True, tracking=True)
    
    luong_van_ban = fields.Selection([
        ('den', 'Văn bản đến'),
        ('di', 'Văn bản đi'),
        ('noi_bo', 'Văn bản nội bộ')
    ], string="Loại văn bản (Luồng)", default='den', required=True)

    hinh_thuc_van_ban = fields.Selection([
        ('cong_van', 'Công văn'),
        ('to_trinh', 'Tờ trình'),
        ('quyet_dinh', 'Quyết định'),
        ('thong_bao', 'Thông báo'),
        ('bao_cao', 'Báo cáo')
    ], string="Thể loại văn bản", default='cong_van', required=True)

    # --- SỬA TẠI ĐÂY: Thêm ondelete='restrict' để bảo vệ hồ sơ số hóa ---
    nhan_vien_id = fields.Many2one('nhan_vien', string="Người soạn thảo/Liên quan", ondelete='restrict')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng liên quan", ondelete='restrict')

    ngay_ban_hanh = fields.Date(string="Ngày ban hành", tracking=True)
    ngay_hieu_luc = fields.Date(string="Ngày hiệu lực", tracking=True)
    
    file_van_ban = fields.Binary(string="Tệp đính kèm")
    file_name = fields.Char(string="Tên tệp")

    trang_thai = fields.Selection([
        ('du_thao', 'Dự thảo'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_ky', 'Đã ký/Ban hành'),
        ('tiep_nhan', 'Tiếp nhận'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('hoan_tat', 'Hoàn tất'),
        ('huy', 'Đã hủy'),
    ], string='Trạng thái', default='du_thao', tracking=True)
    ghi_chu = fields.Html(string="Nội dung chi tiết")

    # --- UI UPGRADE FIELDS & METHODS ---
    display_info_van_ban = fields.Html(compute='_compute_display_info_van_ban', string="Thông tin văn bản")

    def _compute_display_info_van_ban(self):
        for rec in self:
            luong_map = {'den': 'Văn bản ĐẾN', 'di': 'Văn bản ĐI', 'noi_bo': 'Văn bản NỘI BỘ'}
            color_map = {'den': '#3498db', 'di': '#e67e22', 'noi_bo': '#2ecc71'}
            luong_text = luong_map.get(rec.luong_van_ban, 'Văn bản')
            color = color_map.get(rec.luong_van_ban, '#95a5a6')
            
            # Format dates nicely
            ban_hanh_str = rec.ngay_ban_hanh.strftime('%d/%m/%Y') if rec.ngay_ban_hanh else 'Chưa ban hành'
            hieu_luc_str = rec.ngay_hieu_luc.strftime('%d/%m/%Y') if rec.ngay_hieu_luc else 'Chưa hiệu lực'
            
            rec.display_info_van_ban = f"""
                <div style="background: #f8f9fa; border-left: 5px solid {color}; padding: 12px 18px; border-radius: 4px; font-family: 'Segoe UI', Arial, sans-serif; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <span style="font-size: 15px; font-weight: bold; color: #2c3e50;">{rec.ten_van_ban or 'Chưa có nội dung'}</span>
                        <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;">{luong_text}</span>
                    </div>
                    <div style="margin-top: 8px; color: #7f8c8d; font-size: 12px; display: flex; gap: 20px; flex-wrap: wrap;">
                        <span>📂 <b>Số hiệu:</b> {rec.so_hieu or 'Mới'}</span>
                        <span>📅 <b>Ban hành:</b> {ban_hanh_str}</span>
                        <span>📅 <b>Hiệu lực:</b> {hieu_luc_str}</span>
                        <span>👤 <b>Phụ trách:</b> {rec.nhan_vien_id.ho_va_ten or 'Chưa phân công'}</span>
                    </div>
                </div>
            """

    # --- CÁC HÀM XỬ LÝ CHO VĂN BẢN ĐI (WORKFLOW) ---
    
    def action_confirm(self):
        """Hàm Trình duyệt: Chuyển sang chờ duyệt và CẤP MÃ NGAY"""
        for rec in self:
            # Lấy mã số hiệu từ Sequence ngay tại bước này
            seq_code = self.env['ir.sequence'].next_by_code('van_ban.code') or 'Mới'
            rec.write({
                'trang_thai': 'cho_duyet',
                'so_hieu': seq_code  # Không để 'Đang chờ duyệt...' nữa mà gán mã thật luôn
            })

    def action_done(self):
        """Hàm Ký và Ban hành: Chỉ chuyển trạng thái (Mã đã có ở bước trước)"""
        for rec in self:
            rec.write({
                'trang_thai': 'da_ky',
                'ngay_ban_hanh': fields.Date.today()
            })
            # TỰ ĐỘNG HÓA QUY TRÌNH (MỨC 2): Ghi nhận lịch sử tương tác khách hàng
            if rec.khach_hang_id:
                self.env['lich_su_tuong_tac'].create({
                    'khach_hang_id': rec.khach_hang_id.id,
                    'ngay_tuong_tac': fields.Datetime.now(),
                    'loai_hinh': 'khac',
                    'nhan_vien_id': rec.nhan_vien_id.id,
                    'noi_dung': f"Ký và Ban hành văn bản đi: {rec.ten_van_ban} (Số hiệu: {rec.so_hieu})",
                    'ket_qua': 'tot',
                })

    # --- CÁC HÀM XỬ LÝ CHO VĂN BẢN ĐẾN (NEW) ---

    def action_xu_ly(self):
        """Hàm chuyển sang Đang xử lý (Cho văn bản Đến)"""
        for rec in self:
            rec.write({'trang_thai': 'dang_xu_ly'})

    def action_hoan_tat(self):
        """Hàm chuyển sang Hoàn tất và Tự động gửi thông báo nội bộ"""
        for rec in self:
            rec.write({'trang_thai': 'hoan_tat'})
            # TỰ ĐỘNG HÓA QUY TRÌNH (MỨC 2): Ghi nhận lịch sử tương tác khách hàng
            if rec.khach_hang_id:
                self.env['lich_su_tuong_tac'].create({
                    'khach_hang_id': rec.khach_hang_id.id,
                    'ngay_tuong_tac': fields.Datetime.now(),
                    'loai_hinh': 'khac',
                    'nhan_vien_id': rec.nhan_vien_id.id,
                    'noi_dung': f"Hoàn tất xử lý văn bản đến: {rec.ten_van_ban} (Số hiệu: {rec.so_hieu})",
                    'ket_qua': 'tot',
                })
            
            # Nếu là Văn bản nội bộ, hệ thống tự động gửi thông báo cho nhân viên
            if rec.luong_van_ban == 'noi_bo':
                # Tìm tất cả người dùng trong hệ thống (trừ Admin đang thao tác)
                all_users = self.env['res.users'].search([('id', '!=', self.env.user.id)])
                partner_ids = all_users.mapped('partner_id').ids
                
                if partner_ids:
                    # Tạo nội dung thông báo chuyên nghiệp
                    subject = f"🔔 THÔNG BÁO MỚI: {rec.ten_van_ban}"
                    body = f"""
                        <div style="font-family: Arial, sans-serif;">
                            <p>Chào bạn,</p>
                            <p>Công ty vừa ban hành văn bản nội bộ mới với nội dung tóm tắt như sau:</p>
                            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #00A09D;">
                                {rec.ghi_chu}
                            </div>
                            <p style="margin-top: 15px;">Vui lòng kiểm tra chi tiết trên hệ thống Quản lý văn bản.</p>
                            <p>Trân trọng!</p>
                        </div>
                    """
                    # Gửi thông báo vào hệ thống Chatter/Messaging
                    rec.message_post(
                        body=body,
                        subject=subject,
                        partner_ids=partner_ids,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment'
                    )

    def action_cancel(self):
        """Hàm Hủy bỏ"""
        self.write({'trang_thai': 'huy', 'so_hieu': 'Đã hủy'})

    # --- LOGIC TỰ ĐỘNG ---

    @api.model
    def create(self, vals):
        seq_code = self.env['ir.sequence'].next_by_code('van_ban.code') or 'Mới'
        
        # Ép cả văn bản ĐẾN và NỘI BỘ vào Tiếp nhận
        if vals.get('luong_van_ban') in ['den', 'noi_bo']:
            vals['trang_thai'] = 'tiep_nhan'
            vals['so_hieu'] = seq_code
        elif vals.get('luong_van_ban') == 'di':
            vals['trang_thai'] = 'du_thao'
            vals['so_hieu'] = 'Dự thảo'
            
        return super(QuanLyVanBan, self).create(vals)

    def write(self, vals):
        # Tự động xóa khách hàng nếu chuyển loại thành văn bản nội bộ
        if vals.get('luong_van_ban') == 'noi_bo' or (self.luong_van_ban == 'noi_bo' and not vals.get('luong_van_ban')):
            vals['khach_hang_id'] = False
        return super(QuanLyVanBan, self).write(vals)

    def unlink(self):
        # Chặn xóa hồ sơ quan trọng
        for rec in self:
            if rec.trang_thai in ['da_ky', 'hoan_tat']:
                raise UserError(_("Không thể xóa văn bản đã ban hành hoặc đã hoàn tất để bảo vệ hồ sơ số hóa!"))
        return super(QuanLyVanBan, self).unlink()

class KhachHangInherit(models.Model):
    _inherit = 'khach_hang'

    van_ban_ids = fields.One2many(
        'quan_ly_van_ban', 
        'khach_hang_id', 
        string="Văn bản liên quan",
        domain=[('trang_thai', 'in', ['da_ky', 'hoan_tat'])]
    )
    van_ban_count = fields.Integer(string="Số văn bản", compute='_compute_van_ban_count')

    def _compute_van_ban_count(self):
        for rec in self:
            rec.van_ban_count = len(rec.van_ban_ids)

    def action_view_van_ban(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Văn bản liên quan',
            'res_model': 'quan_ly_van_ban',
            'view_mode': 'kanban,tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id},
        }
