```php
<?php
$id = $_GET['id'];
$sql = "SELECT * FROM users WHERE id = $id";
$result = mysqli_query($conn, $sql);
if (!$result) {
    die("Error: " . mysqli_error($conn));
}
$row = mysqli_fetch_assoc($result);
echo $row['username'] . " " . $row['password'];
?>