#!/bin/bash
echo "Masukkan teks yang ingin didekripsi:"
read input
echo "Hasil dekripsi ROT13:"
echo $input | tr 'A-Za-z' 'N-ZA-Mn-za-m'