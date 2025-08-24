```php
<?php
$username = $_GET['username'];
$password = $_GET['password'];

$query = "SELECT * FROM users WHERE username='$username' AND password='$password'";
$result = mysqli_query($conn, $query);

if (mysqli_num_rows($result) > 0) {
    // Login berhasil, tampilkan halaman utama
} else {
    // Login gagal, tampilkan pesan error
}
?>
```