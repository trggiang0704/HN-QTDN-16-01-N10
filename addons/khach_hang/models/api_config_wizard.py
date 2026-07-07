# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApiConfigWizard(models.TransientModel):
    """
    Wizard để cấu hình API Keys cho tính năng AI (Gemini) và Telegram.
    Lưu vào System Parameters để bảo mật.
    """
    _name = 'api.config.wizard'
    _description = 'Cấu hình AI & Telegram API Keys'

    gemini_api_key = fields.Char(
        string="Google Gemini API Key",
        help="Lấy miễn phí tại https://aistudio.google.com/apikey"
    )
    telegram_bot_token = fields.Char(
        string="Telegram Bot Token",
        help="Tạo Bot tại @BotFather, nhắn /newbot"
    )
    telegram_chat_id = fields.Char(
        string="Telegram Chat ID",
        help="ID nhóm/kênh nhận thông báo. Lấy bằng cách vào: https://api.telegram.org/bot{token}/getUpdates"
    )

    def _get_current_values(self):
        """Lấy giá trị hiện tại từ System Parameters"""
        param = self.env['ir.config_parameter'].sudo()
        return {
            'gemini_api_key': param.get_param('ai.gemini_api_key', ''),
            'telegram_bot_token': param.get_param('telegram.bot_token', ''),
            'telegram_chat_id': param.get_param('telegram.chat_id', ''),
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        current = self._get_current_values()
        res.update(current)
        return res

    def action_save_config(self):
        """Lưu API Keys vào System Parameters"""
        param = self.env['ir.config_parameter'].sudo()

        if self.gemini_api_key:
            param.set_param('ai.gemini_api_key', self.gemini_api_key.strip())
        if self.telegram_bot_token:
            param.set_param('telegram.bot_token', self.telegram_bot_token.strip())
        if self.telegram_chat_id:
            param.set_param('telegram.chat_id', self.telegram_chat_id.strip())

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Đã lưu cấu hình thành công!',
                'message': 'API Keys đã được lưu vào System Parameters.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_test_telegram(self):
        """Test kết nối Telegram ngay từ wizard"""
        import requests

        bot_token = self.telegram_bot_token
        chat_id = self.telegram_chat_id

        if not bot_token or not chat_id:
            raise ValidationError(_("Vui lòng điền đầy đủ Bot Token và Chat ID trước khi test!"))

        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            response = requests.post(api_url, json={
                "chat_id": chat_id,
                "text": "✅ *Test kết nối Telegram thành công!*\n\nHệ thống Odoo QLKH đã kết nối và sẵn sàng gửi thông báo.",
                "parse_mode": "Markdown"
            }, timeout=15)
            result = response.json()
        except Exception as e:
            raise ValidationError(_(f"Không thể kết nối Telegram: {str(e)}"))

        if not result.get('ok'):
            raise ValidationError(_(f"Telegram lỗi: {result.get('description', 'Unknown')}"))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '📱 Test Telegram thành công!',
                'message': 'Kiểm tra ứng dụng Telegram của bạn để xem tin nhắn test.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_test_gemini(self):
        """Test kết nối Gemini API ngay từ wizard"""
        import requests
        import json

        api_key = self.gemini_api_key
        if not api_key:
            raise ValidationError(_("Vui lòng điền Gemini API Key trước khi test!"))

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Trả lời bằng tiếng Việt: API đang hoạt động tốt không? Trả lời trong 1 câu."}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 50}
        }

        try:
            response = requests.post(api_url, headers={"Content-Type": "application/json"},
                                     data=json.dumps(payload), timeout=30)
            response.raise_for_status()
            result = response.json()
            ai_reply = result['candidates'][0]['content']['parts'][0]['text']
        except requests.exceptions.HTTPError:
            if response.status_code == 429:
                raise ValidationError(_(
                    "Gemini API đã vượt giới hạn quota!\n"
                    "→ Chờ 1-2 phút rồi thử lại\n"
                    "→ Hoặc tạo API Key mới tại: https://aistudio.google.com/apikey\n"
                    "Gói miễn phí: 15 req/phút, 1500 req/ngày"
                ))
            raise ValidationError(_(f"Lỗi HTTP {response.status_code}: {response.text[:200]}"))
        except Exception as e:
            raise ValidationError(_(f"Lỗi kết nối Gemini: {str(e)}"))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🤖 Gemini API hoạt động!',
                'message': f'Phản hồi AI: {ai_reply[:100]}',
                'type': 'success',
                'sticky': True,
            }
        }
