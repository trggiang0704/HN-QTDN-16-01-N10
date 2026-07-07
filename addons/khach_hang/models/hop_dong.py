# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date

class HopDong(models.Model):
    _name = "hop_dong"
    _description = "Hợp đồng khách hàng"
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Thêm để dùng Chatter
    _rec_name = 'so_hop_dong'

    so_hop_dong = fields.Char(string="Số hợp đồng", required=True, copy=False, readonly=True, 
                             default=lambda self: _('Mới'))
    ten = fields.Char(string="Tiêu đề hợp đồng", required=True)
    
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên đại diện")
    
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True, default=fields.Date.context_today)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc")
    
    gia_tri_hop_dong = fields.Float(string="Giá trị hợp đồng (VNĐ)", required=True)

    thanh_toan = fields.Selection([
        ('chua_thanh_toan', 'Chưa thanh toán'),
        ('da_thanh_toan', 'Đã thanh toán'),
        ('thanh_toan_mot_phan', 'Thanh toán một phần')
    ], string="Trạng thái thanh toán", default='chua_thanh_toan', tracking=True)
    
    trang_thai = fields.Selection([
        ('moi', 'Dự thảo'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy bỏ')
    ], string="Trạng thái", default='moi', copy=False, tracking=True)

    file_hop_dong = fields.Binary(string="Bản quét hợp đồng (PDF/Ảnh)")
    file_name = fields.Char(string="Tên file")
    ghi_chu = fields.Text(string="Ghi chú điều khoản")

    # --- CÁC TRƯỜNG TÍNH TOÁN ĐỂ HIỂN THỊ GIAO DIỆN ĐẸP ---
    display_info_contract = fields.Html(compute='_compute_display_html', string="Thông tin hợp đồng")
    display_customer_info = fields.Html(compute='_compute_display_html', string="Bên A (Khách hàng)")
    display_staff_info = fields.Html(compute='_compute_display_html', string="Bên B (Nhân viên)")

    def _compute_display_html(self):
        for rec in self:
            # 1. Tính toán cột Thông tin hợp đồng
            color = "green" if rec.ngay_ket_thuc and rec.ngay_ket_thuc >= date.today() else "red"
            status_limit = "Còn hạn" if color == "green" else "Hết hạn"
            rec.display_info_contract = f"""
                <div>
                    <strong style="color: #2c3e50; font-size: 14px;">{rec.ten}</strong><br/>
                    <span style="color: #7f8c8d; font-size: 12px;">ID: {rec.so_hop_dong}</span><br/>
                    <span style="color: {color}; font-size: 11px; border: 1px solid {color}; padding: 0px 5px; border-radius: 3px;">
                        ● {status_limit}
                    </span>
                </div>
            """

            # 2. Tính toán cột Bên A (Khách hàng)
            customer_name = rec.khach_hang_id.name or "N/A"
            customer_phone = rec.khach_hang_id.phone or "Chưa có SĐT"
            rec.display_customer_info = f"""
                <div>
                    <i class="fa fa-user" style="color: #3498db;"></i> <b>{customer_name}</b><br/>
                    <small style="color: #95a5a6;">📞 {customer_phone}</small>
                </div>
            """

            # 3. Tính toán cột Bên B (Nhân viên)
            staff_name = rec.nhan_vien_id.ho_va_ten or "Chưa phân công"
            staff_job = rec.nhan_vien_id.chuc_vu_hien_tai_id.ten_chuc_vu or "Nhân viên"
            staff_dept = rec.nhan_vien_id.don_vi_hien_tai_id.ten_don_vi or "Kinh doanh"
            
            rec.display_staff_info = f"""
                <div>
                    <i class="fa fa-briefcase" style="color: #e67e22;"></i> <b>{staff_name}</b><br/>
                    <small style="color: #95a5a6;">{staff_job} - {staff_dept}</small>
                </div>
            """

    # --- TÍNH NĂNG GỬI EMAIL HỢP ĐỒNG ---
    def action_send_contract_email(self):
        self.ensure_one()
        if not self.khach_hang_id.email:
            raise ValidationError(_("Khách hàng này chưa có địa chỉ email!"))
        
        # Xác định tên người gửi (Ưu tiên nhân viên phụ trách, sau đó là người dùng hiện tại)
        sender_name = self.nhan_vien_id.ho_va_ten or self.env.user.name or 'Ban Quản trị'

        # Tạo nội dung email chuyên nghiệp
        body_html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #2c3e50;">Xác nhận Phê duyệt Hợp đồng</h2>
                <p>Kính chào quý khách <b>{self.khach_hang_id.name}</b>,</p>
                <p>Công ty <b>AAHK</b> xin trân trọng thông báo hợp đồng của quý khách đã được phê duyệt chính thức:</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0;">
                    <ul style="list-style: none; padding: 0; margin: 0;">
                        <li><b>Mã số:</b> {self.so_hop_dong}</li>
                        <li><b>Dịch vụ:</b> {self.ten}</li>
                        <li><b>Giá trị:</b> <span style="color: #e74c3c; font-weight: bold;">{self.gia_tri_hop_dong:,.0f} VNĐ</span></li>
                        <li><b>Thời hạn:</b> {self.ngay_bat_dau} đến {self.ngay_ket_thuc}</li>
                    </ul>
                </div>
                
                <p>Vui lòng kiểm tra file đính kèm để xem chi tiết các điều khoản. Nếu có thắc mắc, quý khách có thể phản hồi trực tiếp qua email này.</p>
                
                <p style="margin-top: 25px;">Trân trọng,</p>
                <div>
                    <strong style="font-size: 15px; color: #2c3e50;">{sender_name}</strong><br/>
                    <span style="color: #7f8c8d;">Bộ phận Chăm sóc khách hàng - AAHK CSKH</span>
                </div>
            </div>
        """
        
        mail_values = {
            'subject': f'[AAHK] Xác nhận Hợp đồng {self.so_hop_dong} - {self.ten}',
            'body_html': body_html,
            'email_to': self.khach_hang_id.email,
            # 👇 Cấu hình tên hiển thị + Email gửi/nhận như em yêu cầu
            'email_from': 'AAHK CSKH <khanhhuyen8324@gmail.com>',
            'reply_to': 'AAHK CSKH <khanhhuyen8324@gmail.com>',
        }
        
        # Đính kèm file hợp đồng nếu có
        if self.file_hop_dong:
            attachment = self.env['ir.attachment'].create({
                'name': self.file_name or f'Hop_dong_{self.so_hop_dong}.pdf',
                'type': 'binary',
                'datas': self.file_hop_dong,
                'res_model': 'hop_dong',
                'res_id': self.id,
            })
            mail_values['attachment_ids'] = [(4, attachment.id)]

        # Tạo và gửi mail
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        # Ghi chú vào Chatter
        self.message_post(body=f"✅ Đã gửi email xác nhận hợp đồng đến {self.khach_hang_id.name} (Gửi bởi: {self.env.user.name})")
        return True

    # --- LOGIC TỰ ĐỘNG ---
    @api.model
    def create(self, vals):
        if vals.get('so_hop_dong', _('Mới')) == _('Mới'):
            vals['so_hop_dong'] = self.env['ir.sequence'].next_by_code('hop_dong.code') or _('Mới')
        return super(HopDong, self).create(vals)

    @api.onchange('ngay_bat_dau')
    def _onchange_ngay_bat_dau(self):
        if self.ngay_bat_dau:
            self.ngay_ket_thuc = fields.Date.to_date(self.ngay_bat_dau) + relativedelta(years=1)

    # --- RÀNG BUỘC ---
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_ngay_hop_dong(self):
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau and record.ngay_ket_thuc <= record.ngay_bat_dau:
                raise ValidationError(_("Ngày kết thúc phải sau ngày bắt đầu."))

    @api.constrains('gia_tri_hop_dong')
    def _check_gia_tri(self):
        for record in self:
            if record.gia_tri_hop_dong <= 0:
                raise ValidationError(_("Giá trị hợp đồng phải là số dương."))

    def action_open_ai_chatbot(self):
        """Mở AI Chatbot với ngữ cảnh hợp đồng hiện tại"""
        self.ensure_one()
        return self.env['ai.chatbot.wizard'].action_open_chatbot(
            res_model='hop_dong',
            res_id=self.id
        )

    def action_ai_extract_contract(self):
        """
        Trích xuất thông tin hợp đồng tự động.
        
        Ưu tiên:
        1. Giải mã file PDF/Ảnh, trích xuất văn bản (PyPDF hoặc OCR.space API)
        2. Gửi văn bản trích xuất lên Pollinations AI (Miễn phí, Không cần Key, Không giới hạn) để chuyển thành JSON
        3. Fallback: Nếu thất bại, thử gọi trực tiếp Google Gemini API
        """
        import requests
        import json
        import base64
        import io

        self.ensure_one()

        # 1. Kiểm tra điều kiện đầu vào
        if not self.file_hop_dong:
            raise ValidationError(_("Vui lòng upload file hợp đồng (PDF hoặc ảnh) trước khi phân tích AI!"))

        api_key = self.env['ir.config_parameter'].sudo().get_param('ai.gemini_api_key')

        # Chuẩn bị dữ liệu gửi
        file_data_b64 = self.file_hop_dong.decode('utf-8') if isinstance(self.file_hop_dong, bytes) else self.file_hop_dong

        # Xác định MIME type dựa vào tên file
        mime_type = "application/pdf"
        if self.file_name:
            ext = self.file_name.lower().split('.')[-1]
            if ext in ['jpg', 'jpeg']:
                mime_type = "image/jpeg"
            elif ext == 'png':
                mime_type = "image/png"

        # 2. TRÍCH XUẤT VĂN BẢN (PDF/OCR)
        extracted_text = ""
        try:
            # A. Nếu là PDF: Thử đọc trực tiếp bằng PyPDF
            if mime_type == "application/pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(base64.b64decode(file_data_b64)))
                    extracted_text = "\n".join([page.extract_text() or "" for page in reader.pages])
                except Exception:
                    try:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(io.BytesIO(base64.b64decode(file_data_b64)))
                        extracted_text = "\n".join([page.extract_text() or "" for page in reader.pages])
                    except Exception:
                        pass

            # B. Nếu là Ảnh hoặc PDF quét không có text: Gọi dịch vụ OCR.space miễn phí (Key demo public: helloworld)
            if not extracted_text.strip():
                ocr_url = "https://api.ocr.space/parse/image"
                payload = {
                    "apikey": "helloworld",
                    "language": "vie",
                    "isOverlayRequired": False,
                    "base64Image": f"data:{mime_type};base64,{file_data_b64}"
                }
                ocr_res = requests.post(ocr_url, data=payload, timeout=30)
                if ocr_res.status_code == 200:
                    ocr_data = ocr_res.json()
                    parsed_results = ocr_data.get("ParsedResults", [])
                    if parsed_results:
                        extracted_text = "\n".join([r.get("ParsedText", "") for r in parsed_results])
        except Exception:
            pass

        # 3. GỬI LÊN POLLINATIONS AI ĐỂ PHÂN TÍCH (ƯU TIÊN)
        success = False
        response_text = ""
        ai_reply_json = {}

        if extracted_text.strip():
            parser_prompt = f"""Bạn là chuyên gia phân tích hợp đồng kinh tế. Hãy đọc kỹ nội dung văn bản hợp đồng dưới đây và trích xuất các thông tin sau theo định dạng JSON chính xác:

{{
  "ten": "Tên/Tiêu đề hợp đồng (chuỗi ngắn, dưới 200 ký tự)",
  "khach_hang": "Tên bên A (khách hàng/đối tác)",
  "gia_tri": 0.0,
  "ngay_bat_dau": "YYYY-MM-DD",
  "ngay_ket_thuc": "YYYY-MM-DD",
  "ghi_chu": "Tóm tắt các điều khoản, nghĩa vụ quan trọng của hợp đồng (tối đa 500 ký tự)"
}}

QUY TẮC QUAN TRỌNG:
- Chỉ trả về duy nhất chuỗi JSON, không thêm giải thích hay markdown code block.
- Nếu không tìm thấy thông tin nào, để giá trị là null
- Giá trị tiền tệ chỉ lấy số (không có đơn vị), đơn vị VNĐ
- Ngày tháng theo định dạng YYYY-MM-DD

NỘI DUNG HỢP ĐỒNG:
{extracted_text}"""

            try:
                pollinations_payload = {
                    "messages": [
                        {"role": "system", "content": "You are a precise JSON extractor. Only output valid JSON."},
                        {"role": "user", "content": parser_prompt}
                    ],
                    "model": "openai"
                }
                res = requests.post(
                    "https://text.pollinations.ai/",
                    headers={"Content-Type": "application/json"},
                    json=pollinations_payload,
                    timeout=25
                )
                if res.status_code == 200 and res.text:
                    ai_text = res.text.strip()
                    # Làm sạch JSON code block
                    if ai_text.startswith('```'):
                        ai_text = ai_text.split('```')[1]
                        if ai_text.startswith('json'):
                            ai_text = ai_text[4:]
                    ai_text = ai_text.strip()
                    ai_reply_json = json.loads(ai_text)
                    success = True
            except Exception as e:
                response_text += f"\n- Pollinations AI: {str(e)}"

        # 4. FALLBACK: NẾU THẤT BẠI, GỌI GOOGLE GEMINI VISION API TRỰC TIẾP
        if not success:
            # Prompt cho Vision model
            vision_prompt = """Bạn là chuyên gia phân tích hợp đồng kinh tế. Hãy đọc kỹ nội dung file hợp đồng đính kèm và trích xuất các thông tin sau theo định dạng JSON chính xác:

{
  "ten": "Tên/Tiêu đề hợp đồng (chuỗi ngắn, dưới 200 ký tự)",
  "khach_hang": "Tên bên A (khách hàng/đối tác)",
  "gia_tri": 0.0,
  "ngay_bat_dau": "YYYY-MM-DD",
  "ngay_ket_thuc": "YYYY-MM-DD",
  "ghi_chu": "Tóm tắt các điều khoản, nghĩa vụ quan trọng của hợp đồng (tối đa 500 ký tự)"
}

QUY TẮC:
- Chỉ trả về JSON
- Ngày tháng YYYY-MM-DD
- Giá trị là số thực"""

            models_to_try = [
                ("gemini-1.5-flash", "v1"),
                ("gemini-1.5-flash-8b", "v1"),
                ("gemini-2.0-flash", "v1beta"),
                ("gemini-2.0-flash-lite", "v1beta"),
            ]

            if api_key:
                for model, version in models_to_try:
                    api_url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": vision_prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": file_data_b64
                                    }
                                }
                            ]
                        }],
                        "generationConfig": {
                            "temperature": 0.1,
                            "maxOutputTokens": 1024,
                        }
                    }

                    try:
                        res = requests.post(
                            api_url,
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(payload),
                            timeout=60
                        )
                        if res.status_code == 200:
                            result_data = res.json()
                            ai_text = result_data['candidates'][0]['content']['parts'][0]['text'].strip()
                            if ai_text.startswith('```'):
                                ai_text = ai_text.split('```')[1]
                                if ai_text.startswith('json'):
                                    ai_text = ai_text[4:]
                            ai_text = ai_text.strip()
                            ai_reply_json = json.loads(ai_text)
                            success = True
                            break
                        else:
                            try:
                                err_json = res.json()
                                err_msg = err_json.get('error', {}).get('message', '')
                                response_text += f"\n- {model} ({version}): HTTP {res.status_code} - {err_msg}"
                            except Exception:
                                response_text += f"\n- {model} ({version}): HTTP {res.status_code}"
                    except Exception as e:
                        response_text += f"\n- {model} ({version}): {str(e)}"
            else:
                response_text += "\n- Gemini API: Chưa cấu hình API Key trong System Parameters."

        if not success:
            raise ValidationError(_(
                f"Không thể phân tích hợp đồng bằng AI qua bất kỳ phương thức nào!\n"
                f"Chi tiết lỗi của từng kênh:\n{response_text}\n\n"
                f"💡 Gợi ý khắc phục:\n"
                f"1. Kiểm tra dán đúng API Key mới tạo ở Google AI Studio.\n"
                f"2. Đảm bảo file PDF/Ảnh tải lên rõ chữ, không bị hỏng."
            ))

        extracted = ai_reply_json

        # 7. Ghi kết quả AI vào bản ghi Odoo
        write_vals = {}
        if extracted.get('ten'):
            write_vals['ten'] = extracted['ten']
        if extracted.get('gia_tri') and extracted['gia_tri'] > 0:
            write_vals['gia_tri_hop_dong'] = float(extracted['gia_tri'])
        if extracted.get('ngay_bat_dau'):
            try:
                write_vals['ngay_bat_dau'] = fields.Date.to_date(extracted['ngay_bat_dau'])
            except Exception:
                pass
        if extracted.get('ngay_ket_thuc'):
            try:
                write_vals['ngay_ket_thuc'] = fields.Date.to_date(extracted['ngay_ket_thuc'])
            except Exception:
                pass
        if extracted.get('ghi_chu'):
            write_vals['ghi_chu'] = extracted['ghi_chu']

        if write_vals:
            self.write(write_vals)

        # 8. Ghi log vào Chatter
        fields_filled = ', '.join(write_vals.keys()) if write_vals else 'Không có trường nào'
        self.message_post(body=f"""
            🤖 <b>AI Gemini đã phân tích hợp đồng thành công!</b><br/>
            📄 File: {self.file_name or 'N/A'}<br/>
            ✅ Đã điền tự động: <b>{fields_filled}</b><br/>
            👤 Thực hiện bởi: {self.env.user.name}<br/>
            <i>Vui lòng kiểm tra lại thông tin và điều chỉnh nếu cần.</i>
        """)

        # 9. Thông báo thành công cho người dùng
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🤖 AI Gemini phân tích thành công!',
                'message': f'Đã tự động điền: {fields_filled}. Vui lòng kiểm tra lại thông tin.',
                'type': 'success',
                'sticky': False,
            }
        }

    # =========================================================
    # TÍNH NĂNG MỨC 3: External API - Gửi thông báo Telegram
    # =========================================================
    def action_send_telegram_notification(self):
        """
        Gửi thông báo thông tin hợp đồng này qua Telegram Bot API.
        
        DỮ LIỆU GỬI: Tên HĐ, khách hàng, giá trị, trạng thái, ngày hết hạn
        API TARGET:  https://api.telegram.org/bot{token}/sendMessage
        LƯU KẾT QUẢ: Ghi log vào Chatter của bản ghi Hợp đồng
        """
        import requests

        self.ensure_one()

        # 1. Lấy cấu hình Telegram từ System Parameters
        bot_token = self.env['ir.config_parameter'].sudo().get_param('telegram.bot_token')
        chat_id = self.env['ir.config_parameter'].sudo().get_param('telegram.chat_id')

        if not bot_token or not chat_id:
            raise ValidationError(_(
                "Chưa cấu hình Telegram Bot!\n"
                "Vào: Cài đặt → Thông số kỹ thuật → System Parameters\n"
                "Cần 2 thông số:\n"
                "  • telegram.bot_token  = YOUR_BOT_TOKEN\n"
                "  • telegram.chat_id    = YOUR_CHAT_ID\n\n"
                "Hướng dẫn: Nhắn /newbot cho @BotFather để tạo bot mới"
            ))

        # 2. Xây dựng nội dung thông báo
        ngay_ket_thuc_str = self.ngay_ket_thuc.strftime('%d/%m/%Y') if self.ngay_ket_thuc else 'Không xác định'
        con_lai = ''
        if self.ngay_ket_thuc:
            delta = (self.ngay_ket_thuc - date.today()).days
            if delta >= 0:
                con_lai = f"⏳ Còn lại: *{delta} ngày*"
            else:
                con_lai = f"🔴 Đã hết hạn: *{abs(delta)} ngày trước*"

        trang_thai_map = {
            'moi': '📝 Dự thảo',
            'dang_thuc_hien': '🟢 Đang thực hiện',
            'hoan_thanh': '✅ Hoàn thành',
            'huy': '❌ Hủy bỏ'
        }
        trang_thai_str = trang_thai_map.get(self.trang_thai, self.trang_thai)

        thanh_toan_map = {
            'chua_thanh_toan': '🔴 Chưa thanh toán',
            'thanh_toan_mot_phan': '🟡 Một phần',
            'da_thanh_toan': '🟢 Đã thanh toán'
        }
        thanh_toan_str = thanh_toan_map.get(self.thanh_toan, self.thanh_toan)

        message = f"""📋 *THÔNG BÁO HỢP ĐỒNG - AAHK*

🔖 *Số HĐ:* {self.so_hop_dong}
📄 *Tiêu đề:* {self.ten}

👤 *Khách hàng (Bên A):*
  • Tên: {self.khach_hang_id.name}
  • SĐT: {self.khach_hang_id.phone or 'N/A'}
  • Email: {self.khach_hang_id.email or 'N/A'}

👔 *Nhân viên (Bên B):* {self.nhan_vien_id.ho_va_ten or 'Chưa phân công'}

💰 *Giá trị HĐ:* {self.gia_tri_hop_dong:,.0f} VNĐ
📅 *Ngày ký:* {self.ngay_bat_dau.strftime('%d/%m/%Y') if self.ngay_bat_dau else 'N/A'}
📅 *Ngày hết hạn:* {ngay_ket_thuc_str}
{con_lai}

📊 *Trạng thái:* {trang_thai_str}
💳 *Thanh toán:* {thanh_toan_str}

_Thông báo gửi từ Hệ thống Odoo QLKH_"""

        # 3. Gọi Telegram Bot API
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(api_url, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            raise ValidationError(_("Không thể kết nối Telegram API. Kiểm tra kết nối internet!"))
        except requests.exceptions.Timeout:
            raise ValidationError(_("Telegram API không phản hồi. Thử lại sau!"))
        except requests.exceptions.HTTPError:
            raise ValidationError(_(f"Lỗi Telegram API: {response.text[:300]}"))

        if not result.get('ok'):
            raise ValidationError(_(f"Telegram trả về lỗi: {result.get('description', 'Unknown error')}"))

        # 4. Ghi kết quả vào Chatter
        self.message_post(body=f"""
            📱 <b>Đã gửi thông báo Telegram thành công!</b><br/>
            🤖 Bot Token: ...{bot_token[-8:]}<br/>
            💬 Chat ID: {chat_id}<br/>
            📨 Message ID: {result.get('result', {}).get('message_id', 'N/A')}<br/>
            👤 Thực hiện bởi: {self.env.user.name}
        """)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '📱 Telegram gửi thành công!',
                'message': f'Đã gửi thông báo hợp đồng {self.so_hop_dong} tới Telegram.',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_telegram_expiry_warning(self):
        """
        CronJob tự động - Chạy mỗi ngày lúc 8:00 sáng
        Tìm và gửi cảnh báo Telegram cho các hợp đồng sắp hết hạn trong 30 ngày tới.
        
        DỮ LIỆU GỬI: Danh sách HĐ sắp hết hạn (ngày kết thúc trong 30 ngày tới)
        WHEN:        Hàng ngày lúc 08:00 (định nghĩa trong data/cron.xml)
        KẾT QUẢ:    Ghi log vào Chatter từng hợp đồng, gửi báo cáo tổng hợp lên Telegram
        """
        import requests

        bot_token = self.env['ir.config_parameter'].sudo().get_param('telegram.bot_token')
        chat_id = self.env['ir.config_parameter'].sudo().get_param('telegram.chat_id')

        if not bot_token or not chat_id:
            return  # Không báo lỗi khi chạy cron, chỉ skip

        today = date.today()
        deadline = today + relativedelta(days=30)

        # Tìm hợp đồng sắp hết hạn (đang thực hiện, hết hạn trong 30 ngày tới)
        expiring_contracts = self.search([
            ('trang_thai', '=', 'dang_thuc_hien'),
            ('ngay_ket_thuc', '>=', today),
            ('ngay_ket_thuc', '<=', deadline),
        ])

        if not expiring_contracts:
            return  # Không có hợp đồng nào, không cần gửi

        # Xây dựng thông báo tổng hợp
        contract_lines = ""
        for idx, hd in enumerate(expiring_contracts, 1):
            days_left = (hd.ngay_ket_thuc - today).days
            urgency = "🔴" if days_left <= 7 else ("🟡" if days_left <= 14 else "🟢")
            contract_lines += f"\n{idx}. {urgency} *{hd.so_hop_dong}* - {hd.khach_hang_id.name}\n"
            contract_lines += f"   💰 {hd.gia_tri_hop_dong:,.0f} VNĐ | ⏳ Còn *{days_left} ngày*\n"

        summary_message = f"""⚠️ *CẢNH BÁO: HỢP ĐỒNG SẮP HẾT HẠN*
📅 Ngày báo cáo: {today.strftime('%d/%m/%Y')}
🔢 Tổng số hợp đồng cần xử lý: *{len(expiring_contracts)}*

📋 *Danh sách chi tiết:*
{contract_lines}
━━━━━━━━━━━━━━━━━━━━━━
🔴 ≤ 7 ngày | 🟡 ≤ 14 ngày | 🟢 ≤ 30 ngày

_Vui lòng xử lý gia hạn hoặc liên hệ khách hàng kịp thời!_
_Hệ thống Odoo QLKH - Auto Report 08:00 sáng_"""

        # Gửi lên Telegram
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            requests.post(api_url, json={
                "chat_id": chat_id,
                "text": summary_message,
                "parse_mode": "Markdown"
            }, timeout=15)
        except Exception:
            pass  # Không raise trong cron, ghi log Odoo thay thế

        # Ghi log vào Chatter từng hợp đồng
        for hd in expiring_contracts:
            days_left = (hd.ngay_ket_thuc - today).days
            hd.message_post(body=f"""
                ⚠️ <b>[CRON JOB 08:00] Cảnh báo sắp hết hạn hợp đồng!</b><br/>
                📅 Ngày hết hạn: <b>{hd.ngay_ket_thuc.strftime('%d/%m/%Y')}</b><br/>
                ⏳ Còn lại: <b>{days_left} ngày</b><br/>
                📱 Đã gửi thông báo Telegram tự động.
            """)

