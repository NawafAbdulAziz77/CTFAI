<?php
$username = $_GET['username'];
$password = $_GET['password'];

if ($username == "admin' UNION SELECT flag FROM users--" && $password == "password") {
    echo "#" . $flag;
} else {
    echo "Login gagal.";
}
?>