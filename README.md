# LANGKAH 1: Login ke Server
Buka terminal di komputermu.

SSH ke server kamu:
"ssh -i "keypair.pem" ubuntu@<public-ip-ec2>"

# LANGKAH 2: Update Sistem dan Install Docker

sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose git
sudo systemctl enable docker
sudo systemctl start docker

Verifikasi instalasi Docker:
docker --version
docker-compose --version

# LANGKAH 3: Clone Repository CTFAI
cd /home/ubuntu
git clone https://github.com/NawafAbdulAziz77/CTFAI.git
cd CTFAI
Jika kamu mendapatkan error seperti Permission denied, jalankan:

sudo chown -R ubuntu:ubuntu /home/ubuntu/CTFAI

LANGKAH 4: Jalankan Docker Compose
Pastikan file docker-compose.yml sudah ada di repo kamu. Jalankan:

sudo docker compose up -d
Atau jika pakai versi lama:

sudo docker-compose up -d

# LANGKAH 5: Buka Akses Port

ufw allow openssh

ufw allow http

ufw allow https

ufw enable

# LANGKAH 6: Akses CTFd di Browser
Buka di browser:

http://<public-ip-ec2>
Jika kamu pakai port custom, misalnya 8500:

http://<public-ip-ec2>:8500

# Arahkan IP Server ke Domain
## LANGKAH 1: Arahkan Domain ke IP AWS
Login ke penyedia domain kamu (tempat beli domain ctfai.my.id, misal: Niagahoster, Domainesia, Cloudflare, dsb).
Cari menu DNS Management / DNS Records / Kelola DNS.
Tambahkan DNS record berikut:
Jenis	Host/Name	Value	TTL
A	@	13.219.244.166	default
A	www	13.219.244.166	default

📌 Penjelasan:
@ artinya ctfai.my.id
www artinya www.ctfai.my.id (opsional)

## LANGKAH 2: Uji Coba Arah Domain
Tunggu 1–15 menit (tergantung propagasi DNS), lalu di terminal:
ping ctfai.my.id
Kalau hasilnya menuju IP 13.219.244.166, berarti sudah sukses.

Lalu tes juga:
curl http://ctfai.my.id
Kalau muncul HTML seperti sebelumnya, berarti domain sudah terhubung ke CTFd!

## LANGKAH 3: Update nginx.conf untuk Mengenali Domain
Edit ./conf/nginx/http.conf, ganti ini:
nginx
server_name localhost;
Menjadi:
server_name ctfai.my.id;
Lalu restart nginx:

sudo docker-compose restart nginx

# Buat Soal Kategori Web

## Langkah 1 buat Website Target

Buat website misal HIDDEN Flag in inspect
<!DOCTYPE html>
<html>

<head>
  <!-- Basic -->
  <meta charset="utf-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!-- Mobile Metas -->
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
  <!-- Site Metas -->
  <meta name="keywords" content="" />
  <meta name="description" content="" />
  <meta name="author" content="" />
  <link rel="shortcut icon" href="images/favicon.png" type="">

  <title> Welcome </title>

  <!-- bootstrap core css -->
  <link rel="stylesheet" type="text/css" href="css/bootstrap.css" />

  <!-- fonts style -->
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap" rel="stylesheet">

  <!--owl slider stylesheet -->
  <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css" />

  <!-- font awesome style -->
  <link href="css/font-awesome.min.css" rel="stylesheet" />

  <!-- Custom styles for this template -->
  <link href="css/style.css" rel="stylesheet" />
  <!-- responsive style -->
  <link href="css/responsive.css" rel="stylesheet" />

</head>

<body>

          <div class="detail-box">
            <h5>
              Happy Customers
            </h5>
            <p>
              Incidunt odit rerum tenetur alias architecto asperiores omnis cumque doloribus aperiam numquam! Eligendi corrupti, molestias laborum dolores quod nisi vitae voluptate ipsa? In tempore voluptate ducimus officia id, aspernatur nihil.
              Tempore laborum nesciunt ut veniam, nemo officia ullam repudiandae repellat veritatis unde reiciendis possimus animi autem natus
            </p>
            <p style="visibility: hidden;">Flag : PolinesCTF{1n6eksid1mul41s4k4ran9}</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- end why section -->
</body>

</html>

## Langkah 2 upload pada docker 


