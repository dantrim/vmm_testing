#!/bin/bash
dir=$1
web=$2
title=$3
expresion=$4

#echo "dir : ${dir}"
dir=${dir}for_html/
rm -f $web; touch $web
count=0
echo '<html>' >> $web
echo '<body>' >> $web
echo '<h1> '${title}' </h1>' >> $web
echo '<table border=1>' >> $web
#for file in `ls ${dir}|grep ".eps" | grep ${expresion}`
for file in ${dir}*.png
    do
      #echo $file
      #echo $count
      if((count%3==0))
          then
          echo '<tr><td><a href="'${file}'"><img src="'${file}'" width="350" /></a></td>' >> $web
          #echo '<tr><td><img src="'${file}'" width="350" /></td>' >> $web
          #echo '<tr><td><img src="'${dir}'/'${file}'" width="350" /></td>' >> $web
      fi
      if((count%3==1))
          then
          echo '<td><a href="'${file}'"><img src="'${file}'" width="350" /></a></td>' >> $web
          #echo '<td><img src="'${file}'" width="350" /></td>' >> $web
          #echo '<td><img src="'${dir}'/'${file}'" width="350" /></td>' >> $web
      fi
      if((count%3==2))
          then
          echo '<td><a href="'${file}'"><img src="'${file}'" width="350" /></a></td></tr>' >> $web
          #echo '<td><img src="'${file}'" width="350" /></td></tr>' >> $web
          #echo '<td><img src="'${dir}'/'${file}'" width="350" /></td></tr>' >> $web
      fi
      count=`expr $count + 1`
    done
echo "</table>" >> $web
echo "</body>" >> $web
echo "</html>" >> $web
