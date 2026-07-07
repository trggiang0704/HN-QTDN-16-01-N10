# -*- coding: utf-8 -*-
{
    'name': "Quản lý khách hàng mới",
    'version': '1.0',
    'depends': ['base', 'mail', 'nhan_su'],
    # 'depends': ['base', 'mail', 'nhan_su'],
    # 'depends': ['base', 'mail', 'nhan_su'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/cron.xml',
        'views/khach_hang_dashboard.xml',
        'views/khach_hang.xml',
        'views/hop_dong.xml',
        'views/ho_tro.xml',
        'views/bao_gia.xml',
        'views/api_config_wizard.xml',
        'views/ai_chatbot_wizard.xml',
        'data/mail_template_data.xml',
        # 'views/khach_hang_tn.xml',
        'views/menu.xml',
        # Em có thể tạo thêm file views/menu.xml sau hoặc dán chung vào khach_hang.xml
    ],
    'assets': {
        'web.assets_backend': [
            'khach_hang/static/src/css/kanban_custom.css',
        ],
    },
    'installable': True,
    'application': True,
}
