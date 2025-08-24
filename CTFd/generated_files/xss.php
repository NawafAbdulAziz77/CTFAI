```php
<?php
  $name = $_POST['name'];
  echo "<html><body><h1>Hello, $name!</h1><script>document.write(document.cookie);</script></body></html>";
?>
```