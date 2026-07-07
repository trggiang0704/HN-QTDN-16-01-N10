# -*- coding: utf-8 -*-
import json
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AIChatbotWizard(models.TransientModel):
    """
    AI Chatbot Wizard - Hỏi đáp thông minh dựa trên dữ liệu nội bộ Odoo.
    
    MỨC 3 - AI:
    - INPUT:  Câu hỏi từ người dùng về khách hàng, hợp đồng, hoặc quy trình nội bộ
    - XỬ LÝ: Gemini API phân tích câu hỏi + ngữ cảnh dữ liệu Odoo
    - OUTPUT: Câu trả lời dựa trên dữ liệu thực của hệ thống
    """
    _name = 'ai.chatbot.wizard'
    _description = 'AI Chatbot - Hỏi đáp thông minh'

    question = fields.Char(string="Câu hỏi của bạn", placeholder="Ví dụ: Khách hàng này có bao nhiêu hợp đồng đang thực hiện?")
    chat_history = fields.Html(string="Lịch sử trò chuyện", readonly=True)
    messages_json = fields.Text(string="Messages JSON", default='[]')
    context_type = fields.Selection([
        ('customer', 'Khách hàng cụ thể'),
        ('contract', 'Hợp đồng cụ thể'),
        ('general', 'Nghiệp vụ chung'),
    ], string="Ngữ cảnh", default='general')
    res_model = fields.Char(string="Model tham chiếu")
    res_id = fields.Integer(string="ID bản ghi")

    def _build_system_context(self):
        """
        Xây dựng ngữ cảnh nội bộ từ Odoo để đưa vào prompt AI.
        AI sẽ dựa vào dữ liệu thực này để trả lời câu hỏi.
        """
        context_lines = []
        context_lines.append("=== DỮ LIỆU NỘI BỘ HỆ THỐNG QLKH ===")

        # Thống kê tổng quan
        total_kh = self.env['khach_hang'].search_count([])
        total_hd = self.env['hop_dong'].search_count([])
        hd_active = self.env['hop_dong'].search_count([('trang_thai', '=', 'dang_thuc_hien')])
        hd_hoan_thanh = self.env['hop_dong'].search_count([('trang_thai', '=', 'hoan_thanh')])
        total_bao_gia = self.env['bao_gia'].search_count([])
        total_ho_tro = self.env['ho_tro_khach_hang'].search_count([])

        context_lines.append(f"\n[THỐNG KÊ TỔNG QUAN]")
        context_lines.append(f"- Tổng số khách hàng: {total_kh}")
        context_lines.append(f"- Tổng số hợp đồng: {total_hd} (Đang thực hiện: {hd_active}, Hoàn thành: {hd_hoan_thanh})")
        context_lines.append(f"- Tổng số báo giá: {total_bao_gia}")
        context_lines.append(f"- Tổng yêu cầu hỗ trợ: {total_ho_tro}")

        # Thông tin bản ghi cụ thể nếu có
        if self.res_model == 'khach_hang' and self.res_id:
            kh = self.env['khach_hang'].browse(self.res_id)
            if kh.exists():
                context_lines.append(f"\n[THÔNG TIN KHÁCH HÀNG ĐANG XEM]")
                context_lines.append(f"- Mã KH: {kh.ma_khach_hang}")
                context_lines.append(f"- Tên: {kh.name}")
                context_lines.append(f"- Giai đoạn: {dict(kh._fields['giai_doan'].selection).get(kh.giai_doan, 'N/A')}")
                context_lines.append(f"- SĐT: {kh.phone or 'Chưa có'}")
                context_lines.append(f"- Email: {kh.email or 'Chưa có'}")
                context_lines.append(f"- Địa chỉ: {kh.address or 'Chưa có'}")
                context_lines.append(f"- Doanh thu tiềm năng: {kh.doanh_thu_tiem_nang:,.0f} VNĐ")
                context_lines.append(f"- Nhân viên phụ trách: {kh.nhan_vien_id.ho_va_ten if kh.nhan_vien_id else 'Chưa phân công'}")
                context_lines.append(f"- Số hợp đồng: {len(kh.hop_dong_ids)}")
                context_lines.append(f"- Số báo giá: {len(kh.bao_gia_ids)}")
                context_lines.append(f"- Số lần tương tác: {len(kh.lich_su_ids)}")

                # Danh sách hợp đồng
                if kh.hop_dong_ids:
                    context_lines.append(f"\n[HỢP ĐỒNG CỦA KHÁCH HÀNG]")
                    for hd in kh.hop_dong_ids[:5]:
                        context_lines.append(
                            f"  • {hd.so_hop_dong}: {hd.ten} | "
                            f"Giá trị: {hd.gia_tri_hop_dong:,.0f} VNĐ | "
                            f"Trạng thái: {dict(hd._fields['trang_thai'].selection).get(hd.trang_thai, '')} | "
                            f"Hết hạn: {hd.ngay_ket_thuc or 'N/A'}"
                        )

        elif self.res_model == 'hop_dong' and self.res_id:
            hd = self.env['hop_dong'].browse(self.res_id)
            if hd.exists():
                context_lines.append(f"\n[THÔNG TIN HỢP ĐỒNG ĐANG XEM]")
                context_lines.append(f"- Số HĐ: {hd.so_hop_dong}")
                context_lines.append(f"- Tiêu đề: {hd.ten}")
                context_lines.append(f"- Khách hàng: {hd.khach_hang_id.name}")
                context_lines.append(f"- Nhân viên: {hd.nhan_vien_id.ho_va_ten if hd.nhan_vien_id else 'N/A'}")
                context_lines.append(f"- Giá trị: {hd.gia_tri_hop_dong:,.0f} VNĐ")
                context_lines.append(f"- Ngày bắt đầu: {hd.ngay_bat_dau}")
                context_lines.append(f"- Ngày kết thúc: {hd.ngay_ket_thuc or 'Không xác định'}")
                context_lines.append(f"- Trạng thái: {dict(hd._fields['trang_thai'].selection).get(hd.trang_thai, '')}")
                context_lines.append(f"- Thanh toán: {dict(hd._fields['thanh_toan'].selection).get(hd.thanh_toan, '')}")
                if hd.ghi_chu:
                    context_lines.append(f"- Ghi chú điều khoản: {hd.ghi_chu[:300]}")

        # Thống kê Nhân sự
        total_nv = self.env['nhan_vien'].search_count([])
        nv_working = self.env['nhan_vien'].search_count([('trang_thai', '=', 'working')])
        nv_leave = self.env['nhan_vien'].search_count([('trang_thai', '=', 'leave')])
        
        context_lines.append(f"\n[THỐNG KÊ NHÂN SỰ & PHÒNG BAN]")
        context_lines.append(f"- Tổng số nhân sự: {total_nv} (Đang làm việc: {nv_working}, Tạm nghỉ: {nv_leave})")
        
        # Danh sách Đơn vị / Phòng ban
        don_vis = self.env['don_vi'].search([])
        if don_vis:
            context_lines.append("- Các đơn vị phòng ban:")
            for dv in don_vis:
                context_lines.append(f"  • {dv.ten_don_vi} (Mã: {dv.ma_don_vi or ''})")
                
        # Danh sách Chức vụ
        chuc_vus = self.env['chuc_vu'].search([])
        if chuc_vus:
            context_lines.append("- Các chức vụ chính: " + ", ".join([cv.ten_chuc_vu for cv in chuc_vus]))

        # Chi tiết nhân viên đang hoạt động
        active_staff = self.env['nhan_vien'].search([('trang_thai', '=', 'working')], limit=20)
        if active_staff:
            context_lines.append(f"\n[DANH SÁCH NHÂN VIÊN ĐANG HOẠT ĐỘNG]")
            for nv in active_staff:
                chuc_vu = nv.chuc_vu_hien_tai_id.ten_chuc_vu if nv.chuc_vu_hien_tai_id else 'Nhân viên'
                don_vi = nv.don_vi_hien_tai_id.ten_don_vi if nv.don_vi_hien_tai_id else 'Chưa gán đơn vị'
                context_lines.append(
                    f"  • {nv.ho_va_ten} ({nv.ma_dinh_danh}) | "
                    f"Chức vụ: {chuc_vu} | Phòng ban: {don_vi} | "
                    f"SĐT: {nv.so_dien_thoai or 'N/A'} | Email: {nv.email or 'N/A'}"
                )

        # Quy trình nội bộ
        context_lines.append(f"\n[QUY TRÌNH NGHIỆP VỤ NỘI BỘ]")
        context_lines.append("- Giai đoạn CRM: Tiếp cận → Đã kết nối → Đàm phán → Ký hợp đồng → Thành công")
        context_lines.append("- Trạng thái hợp đồng: Dự thảo → Đang thực hiện → Hoàn thành (hoặc Hủy bỏ)")
        context_lines.append("- Trạng thái thanh toán: Chưa thanh toán / Một phần / Đã thanh toán")
        context_lines.append("- Hệ thống gửi email xác nhận khi hợp đồng được ký")
        context_lines.append("- Hệ thống gửi Telegram cảnh báo khi HĐ sắp hết hạn (≤30 ngày)")
        context_lines.append("- Văn bản ban hành không được xóa khỏi hệ thống")

        return "\n".join(context_lines)

    def _render_chat_html(self, messages):
        """Render lịch sử chat thành HTML đẹp"""
        if not messages:
            return """
            <div style="text-align: center; padding: 40px; color: #94a3b8;">
                <i class="fa fa-comments" style="font-size: 40px; margin-bottom: 15px; display: block;"></i>
                <p style="font-size: 14px;">Chào bạn! Tôi là AI Trợ lý QLKH 🤖</p>
                <p style="font-size: 12px;">Hãy hỏi tôi về khách hàng, hợp đồng, báo giá hoặc quy trình nghiệp vụ!</p>
            </div>
            """

        html_parts = ['<div style="font-family: Segoe UI, Arial, sans-serif; padding: 10px;">']
        for msg in messages:
            if msg['role'] == 'user':
                html_parts.append(f"""
                <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                    <div style="max-width: 75%; background: linear-gradient(135deg, #3b82f6, #2563eb);
                                color: white; padding: 10px 15px; border-radius: 18px 18px 4px 18px;
                                font-size: 13px; line-height: 1.5; box-shadow: 0 2px 8px rgba(59,130,246,0.3);">
                        <strong>👤 Bạn:</strong><br/>{msg['content']}
                    </div>
                </div>
                """)
            else:
                content_html = msg['content'].replace('\n', '<br/>')
                html_parts.append(f"""
                <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                    <div style="max-width: 80%; background: #f1f5f9; border: 1px solid #e2e8f0;
                                color: #1e293b; padding: 10px 15px; border-radius: 18px 18px 18px 4px;
                                font-size: 13px; line-height: 1.6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <strong style="color: #7c3aed;">🤖 AI Trợ lý:</strong><br/>{content_html}
                    </div>
                </div>
                """)
        html_parts.append('</div>')
        return ''.join(html_parts)

    def action_send_question(self):
        """
        Gửi câu hỏi đến Gemini API và nhận câu trả lời dựa trên dữ liệu nội bộ Odoo.
        
        INPUT:  Câu hỏi từ người dùng (self.question)
        XỬ LÝ: Gemini API + System Context từ database Odoo
        OUTPUT: Câu trả lời cập nhật vào chat_history, messages_json
        """
        import requests

        if not self.question or not self.question.strip():
            raise ValidationError(_("Vui lòng nhập câu hỏi!"))

        api_key = self.env['ir.config_parameter'].sudo().get_param('ai.gemini_api_key')
        if not api_key:
            raise ValidationError(_(
                "Chưa cấu hình Gemini API Key!\n"
                "Vào menu: Quản lý Khách hàng → Cấu hình → ⚙️ Cấu hình AI & Telegram"
            ))

        # Load lịch sử chat
        messages = json.loads(self.messages_json or '[]')
        user_question = self.question.strip()

        # Xây dựng system prompt với dữ liệu nội bộ
        internal_context = self._build_system_context()
        system_prompt = f"""Bạn là AI Trợ lý thông minh của hệ thống Quản lý Khách hàng (QLKH) AAHK.

{internal_context}

=== HƯỚNG DẪN TRẢ LỜI ===
- Chỉ sử dụng dữ liệu nội bộ ở trên để trả lời
- Trả lời ngắn gọn, chính xác, bằng tiếng Việt
- Nếu không có dữ liệu, hãy thành thật nói không tìm thấy
- Đưa ra gợi ý hữu ích dựa trên ngữ cảnh
- Format rõ ràng bằng bullet points khi cần liệt kê"""

        # Xây dựng conversation history cho API
        api_contents = []
        # Đưa system context vào lượt đầu
        api_contents.append({
            "role": "user",
            "parts": [{"text": system_prompt + "\n\nBắt đầu cuộc trò chuyện. Hãy chào và sẵn sàng hỗ trợ."}]
        })
        api_contents.append({
            "role": "model",
            "parts": [{"text": "Xin chào! Tôi là AI Trợ lý QLKH. Tôi đã đọc dữ liệu hệ thống và sẵn sàng hỗ trợ bạn. Bạn có câu hỏi gì không?"}]
        })

        # Thêm lịch sử trò chuyện trước
        for msg in messages[-10:]:  # Giữ tối đa 10 lượt gần nhất
            role = "user" if msg['role'] == 'user' else "model"
            api_contents.append({
                "role": role,
                "parts": [{"text": msg['content']}]
            })

        # Thêm câu hỏi hiện tại
        api_contents.append({
            "role": "user",
            "parts": [{"text": user_question}]
        })

        # =========================================================
        # CƠ CHẾ KẾT NỐI AI: ƯU TIÊN POLLINATIONS AI (Miễn phí, Không cần Key, Không giới hạn)
        # Nếu thất bại sẽ tự động chuyển sang cấu hình Google Gemini API
        # =========================================================
        ai_answer = ""
        success = False
        last_error_details = ""

        # Lịch sử chat theo định dạng chuẩn OpenAI
        openai_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "Xin chào! Tôi là AI Trợ lý QLKH. Tôi đã đọc dữ liệu hệ thống và sẵn sàng hỗ trợ bạn. Bạn có câu hỏi gì không?"}
        ]
        for msg in messages[-8:]:
            role = "user" if msg['role'] == 'user' else "assistant"
            openai_messages.append({"role": role, "content": msg['content']})
        openai_messages.append({"role": "user", "content": user_question})

        # 1. THỬ DÙNG POLLINATIONS AI (Bypass hoàn toàn quota/key)
        try:
            pollinations_payload = {
                "messages": openai_messages,
                "model": "openai",  # Sử dụng GPT-4o được host miễn phí bởi Pollinations AI
                "jsonMode": False
            }
            response = requests.post(
                "https://text.pollinations.ai/",
                headers={"Content-Type": "application/json"},
                json=pollinations_payload,
                timeout=20
            )
            if response.status_code == 200 and response.text:
                ai_answer = response.text
                success = True
        except Exception as e:
            last_error_details += f"<br/>• <b>Pollinations AI (Keyless)</b>: {str(e)}"

        # 2. THỬ DÙNG GOOGLE GEMINI (Nếu Pollinations thất bại)
        if not success and api_key:
            models_to_try = [
                ("gemini-1.5-flash", "v1"),
                ("gemini-1.5-flash-8b", "v1"),
                ("gemini-2.0-flash", "v1beta"),
                ("gemini-2.0-flash-lite", "v1beta"),
            ]

            for model, version in models_to_try:
                api_url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": api_contents,
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 800,
                    }
                }
                try:
                    response = requests.post(
                        api_url,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                        timeout=15
                    )
                    if response.status_code == 200:
                        result = response.json()
                        ai_answer = result['candidates'][0]['content']['parts'][0]['text']
                        success = True
                        break
                    else:
                        try:
                            err_json = response.json()
                            err_msg = err_json.get('error', {}).get('message', '')
                            err_status = err_json.get('error', {}).get('status', '')
                            last_error_details += f"<br/>• <b>{model} ({version})</b>: HTTP {response.status_code} ({err_status}) - {err_msg}"
                        except Exception:
                            last_error_details += f"<br/>• <b>{model} ({version})</b>: HTTP {response.status_code} - {response.text[:150]}"
                except Exception as e:
                    last_error_details += f"<br/>• <b>{model} ({version})</b>: {str(e)}"

        if not success:
            ai_answer = (
                f"⚠️ <b>Không thể kết nối với dịch vụ AI!</b><br/>"
                f"Các kênh dịch vụ đều báo lỗi:<br/>"
                f"{last_error_details}<br/><br/>"
                f"💡 <i>Gợi ý khắc phục: Kiểm tra lại kết nối internet của máy chủ Odoo/WSL.</i>"
            )

        # Lưu lịch sử
        messages.append({'role': 'user', 'content': user_question})
        messages.append({'role': 'assistant', 'content': ai_answer})

        # Cập nhật wizard
        self.write({
            'messages_json': json.dumps(messages, ensure_ascii=False),
            'chat_history': self._render_chat_html(messages),
            'question': '',  # Xóa ô nhập sau khi gửi
        })

        # Reload wizard (giữ nguyên cửa sổ)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.chatbot.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('khach_hang.view_ai_chatbot_wizard_form').id,
            'target': 'new',
        }

    def action_clear_chat(self):
        """Xóa lịch sử trò chuyện"""
        self.write({
            'messages_json': '[]',
            'chat_history': False,
            'question': '',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.chatbot.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('khach_hang.view_ai_chatbot_wizard_form').id,
            'target': 'new',
        }

    @api.model
    def action_open_chatbot(self, res_model=None, res_id=None):
        """Mở chatbot từ bất kỳ đâu với ngữ cảnh tùy chọn"""
        wizard = self.create({
            'res_model': res_model or '',
            'res_id': res_id or 0,
            'context_type': 'customer' if res_model == 'khach_hang' else (
                'contract' if res_model == 'hop_dong' else 'general'
            ),
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.chatbot.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': self.env.ref('khach_hang.view_ai_chatbot_wizard_form').id,
            'target': 'new',
        }
