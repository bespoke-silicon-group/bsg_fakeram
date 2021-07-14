if ! grep -Fxq '//  else if (F_sz_um > 0.091)' ./tools/cacti/io.cc
then
 sed -i '/else if (F_sz_um > 0.091)/,/\}/'' s/^/\/\//' ./tools/cacti/io.cc
fi
