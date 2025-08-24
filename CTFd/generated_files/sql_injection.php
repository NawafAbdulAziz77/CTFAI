```php
<?php
$username = $_POST['username'];
$password = $_POST['password'];

$query = "SELECT * FROM users WHERE username = '$username' AND password = '$password'";
$result = mysqli_query($conn, $query);

if(mysqli_num_rows($result) > 0){
    echo "Login berhasil";
} else {
    echo "Login gagal";
}
?>