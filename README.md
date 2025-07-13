✅ LANGKAH 1: Login ke EC2 Instance
Buka terminal di komputermu.

SSH ke server AWS EC2 kamu:
ssh -i "keypair.pem" ubuntu@<public-ip-ec2>

✅ LANGKAH 2: Update Sistem dan Install Docker

sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose git
sudo systemctl enable docker
sudo systemctl start docker
Verifikasi instalasi Docker:

docker --version
docker-compose --version

✅ LANGKAH 3: Clone Repository CTFd
cd /home/ubuntu
git clone https://github.com/NawafAbdulAziz77/CTFAI.git
cd CTFAI
Jika kamu mendapatkan error seperti Permission denied, jalankan:

sudo chown -R ubuntu:ubuntu /home/ubuntu/CTFAI

✅ LANGKAH 4: Jalankan Docker Compose
Pastikan file docker-compose.yml sudah ada di repo kamu. Jalankan:

sudo docker compose up -d
Atau jika pakai versi lama:

sudo docker-compose up -d

✅ LANGKAH 5: Buka Akses Port di AWS
Masuk ke AWS EC2 → Instances → Pilih instance kamu.

Klik Security → Security Groups → Klik nama security group.

Masuk ke tab Inbound Rules → Klik Edit Inbound Rules.

Tambahkan rule:

Type: HTTP

Port Range: 80

Source: Anywhere (0.0.0.0/0)

Kalau kamu expose port lain, misalnya 8000 atau 8500, tambahkan juga rule untuk port itu.

✅ LANGKAH 6: Akses CTFd di Browser
Buka di browser:

http://<public-ip-ec2>
Jika kamu pakai port custom, misalnya 8500:

http://<public-ip-ec2>:8500


Keren! ✅ Kamu sudah punya domain ctfai.my.id — itu langkah awal yang sangat bagus.

Sekarang tinggal menghubungkan domain ke CTFd kamu yang jalan di AWS, dan (opsional) pasang HTTPS biar lebih aman dan terpercaya.

🎯 Tujuan
Membuat http://ctfai.my.id (atau https://ctfai.my.id) mengarah ke CTFd kamu di 13.219.244.166.

✅ LANGKAH 1: Arahkan Domain ke IP AWS
Login ke penyedia domain kamu (tempat beli domain ctfai.my.id, misal: Niagahoster, Domainesia, Cloudflare, dsb).
Cari menu DNS Management / DNS Records / Kelola DNS.
Tambahkan DNS record berikut:
Jenis	Host/Name	Value	TTL
A	@	13.219.244.166	default
A	www	13.219.244.166	default

📌 Penjelasan:
@ artinya ctfai.my.id
www artinya www.ctfai.my.id (opsional)

✅ LANGKAH 2: Uji Coba Arah Domain
Tunggu 1–15 menit (tergantung propagasi DNS), lalu di terminal:
ping ctfai.my.id
Kalau hasilnya menuju IP 13.219.244.166, berarti sudah sukses.

Lalu tes juga:
curl http://ctfai.my.id
Kalau muncul HTML seperti sebelumnya, berarti domain sudah terhubung ke CTFd!

✅ LANGKAH 3: Update nginx.conf untuk Mengenali Domain
Edit ./conf/nginx/http.conf, ganti ini:
nginx
server_name localhost;
Menjadi:
server_name ctfai.my.id;
Lalu restart nginx:

sudo docker-compose restart nginx
