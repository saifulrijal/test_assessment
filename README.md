# test_assessment
Skill Task Platform Odoo Engineer

# project_api
installasi : 
1. masuk aplikasi apps
2. masukkan kata pencarian project_api
3. pilih tombol install, tunggu sampai proses selesai

export data user baru di odoo:
1. user sudah mempunya akses setting
2. masuk applikasi settings pilih menu user & companies
3. pilih menu user di dalam sub menu user & companies
4. pilih icon export yang terletak di sebelah menu create
5. setelah file terdownload, bisa menambahkan user baru kedalam file yang sudah terdownload

import data user baru di odoo:
1. user sudah mempunya akses setting
2. masuk applikasi settings pilih menu user & companies
3. pilih menu user di dalam sub menu user & companies
4. pilih icon binatng atau favorites
5. pilih import record
6. pilih load file, masukkan file yang terdownload dari hasil export data user
7. pilih menu import

menaktivasi multi currency : 
1. masuk applikasi settings pilih menu user & companies
2. pilih salah satu admin untuk diberikan akses multi currencies dengan cara mencentang kolom multi currencieslalu pilih save
3. masuk applikasi accounting
4. pilih menu configuration -> settings
5. centang multi-currencies
6. centang automatic currency rates
 
 memilih currency yang active:
 1. pastikan user sudah mempunyai akses multi currency
 2. masuk applikasi accounting pilih menu configuration
 3. didalam sub menu configuration pilih currency
 4. pilih currency yang akan di aktive kan

 untuk aktivasi atau arcive scheduler / cron fungsi update multi currencies:
 1. pastikan sudah 
 1. masuk applikasi settings
 2. pilih menu technical kemudian plih schedule actions
 3. pilih record multy currency

mendapatkan token dari odoo:
1. mengirim data ke url /api/login dengan header 
    {
        'login': login odoo,
        'password': password login odoo,
        'db': db yang active sekarang,
        'content-type': 'text/plain'
    }
2 informasi yang didapatkan setelah mengirm data
{
    "uid": 2,
    "user_context": {
        "lang": "en_AU",
        "tz": "Asia/Jakarta",
        "uid": 2
    },
    "company_id": 1,
    "company_ids": [
        2,
        1
    ],
    "partner_id": 3,
    "access_token": "access_token_86500463eb573b57fe07a75f9400e8a166c4bc75",
    "company_name": "YourCompany",
    "country": "United States",
    "contact_address": "YourCompany\n215 Vine St\n\nScranton PA 18503\nUnited States"
}

membuat sale order dengan API ke Odoo:
1. mengirim data ke url /api/create/order dengan header dan body seperti berikut:
    header :
    {
        'access_token': token yang didapat dari odoo,
    }
    body: 
    {
        'partner_id': {
            'name': 'Contoh Partner',
            'email': 'example@partner.com',
            'phone': '08123456789',
            'uuid': "d992453e"
        },
        'order_line': [
            {
                'product_id': {
                    "uuid": "d992453e-c26e-48d6-bedc-92bc55f8585e",
                    "komoditas": "BANDENG",
                    "area_provinsi": "SULAWESI BARAT",
                    "area_kota": "MAMUJU UTARA",
                    "size": "180",
                    "price": "29000",
                    "tgl_parsed": "2022-01-01T19:08:13Z",
                    "timestamp": "1641064093344",
                },
                'name': 'BANDENG',
                'qty': 12,
                'price_unit': 29000
            }
        ]

    }
    untuk orderline nya bisa lebih dari 1 record
2. setelah sale order terbuat akan langsung di confirm
3. seletelah terconfirm sale order akan membuat invoice dan langsung di confirm
4. setelah terconfirm akan membuat register payment automatis sehingga data invoice nya sudah terbayar
