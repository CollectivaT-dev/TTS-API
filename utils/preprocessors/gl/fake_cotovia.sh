infile=$1

dirname=$(dirname -- "$infile")
filename=$(basename -- "$infile")
extension="${filename##*.}"
filename="${filename%.*}"

echo "o^ Gale^Go" > $dirname/$filename.tra
echo "e^ u^Na li^Ngwa" >> $dirname/$filename.tra