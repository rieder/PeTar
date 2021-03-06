#!/bin/bash

until [[ `echo x$1` == 'x' ]]
do
    case $1 in
	-h) shift;
	    echo 'PeTar initial data file generator, convert input data file to petar input'
	    echo 'input (origin) data file (mass, position[3], velocity[3] per line; 7 columns)';
	    echo 'Usage: petar.init [options] [input data filename]';
	    echo 'Options:';
	    echo '  -f: output file (petar input data) name (default: intput file name + ".input")';
	    echo '  -i: skip rows number (default: 0)';
	    echo '  -s: stellar evolution columns:  base | bse | no (default: no)';
	    echo '  -m: mass scaling factor from input data unit to [Msun], used for stellar evolution (BSE): mass[input unit]*m_scale=mass[Msun] (default: 1.0)';
	    echo '  -r: radius scaling factor from input data unit to [pc] (default: 1.0)';
	    echo '  -v: velocity scaling factor from input data unit to [pc/myr]. If the string "kms2pcmyr" is given, convert velocity unit from [km/s] to [pc/myr] (default: 1.0)';
	    echo '  -u: calculate the velocity scaling factor based on -m and -r, then convert data unit to (Msun, pc, pc/myr), input data should use the Henon unit (total mass=1, G=1)';
	    echo '  -c: add position and velocity offset to all particles [input unit], values are separated by "," (0,0,0,0,0,0)';
	    echo '  -R: initial stellar radius for "-s base" mode (default: 0.0)';
	    exit;;
	-f) shift; fout=$1; shift;;
	-i) shift; igline=$1; shift;;
	-s) shift; seflag=$1; shift;;
	-m) shift; mscale=$1; convert=1; shift;;
	-r) shift; rscale=$1; convert=1; shift;;
	-v) shift; vscale=$1; convert=1; shift;;
	-u) convert=2; shift;;
	-R) shift; radius=$1; shift;;
	-c) shift; cm=$1; shift;;
	*) fname=$1;shift;;
    esac
done

if [ ! -e $fname ] | [ -z $fname ] ; then
    echo 'Error, file name not provided' 
    exit
fi
[ -z $fout ] && fout=$fname.input
[ -z $igline ] && igline=0
[ -z $seflag ] && seflag='no'
[ -z $rscale ] && rscale=1.0
[ -z $mscale ] && mscale=1.0
[ -z $vscale ] && vscale=1.0
[ -z $radius ] && radius=0.0
[ -z $convert ] && convert=0
[ -z $cm ] && cm='none'

echo 'Transfer "'$fname'" to PeTar input data file "'$fout'"'
echo 'Skip rows: '$igline
echo 'Add stellar evolution columns: '$seflag

n=`wc -l $fname|cut -d' ' -f1`
n=`expr $n - $igline`

# add offset and remove skiprows
if [[ $cm != 'none' ]]; then
    cm_array=(`echo $cm|sed 's/,/ /g'`)
    echo 'offset: pos: '${cm_array[0]}' '${cm_array[1]}' '${cm_array[2]}' vel: '${cm_array[3]}' '${cm_array[4]}' '${cm_array[5]}
    awk -v ig=$igline -v x=${cm_array[0]} -v y=${cm_array[1]} -v z=${cm_array[2]} -v vx=${cm_array[3]} -v vy=${cm_array[4]} -v vz=${cm_array[5]} '{OFMT="%.15g"; if(NR>ig) print $1,$2+x,$3+y,$4+z,$5+vx,$6+vy,$7+vz}' $fname > $fname.off__
else
    awk -v ig=$igline '{if(NR>ig) print $LINE}' $fname >$fname.off__
fi

# first, scale data
if [ $convert == 2 ]; then
    G=0.00449830997959438
    echo 'Convert Henon unit to Astronomical unit: distance scale: '$rscale';  mass scale: '$mscale';  velocity scale: sqrt(G*ms/rs);  G='$G
    awk -v rs=$rscale -v G=$G -v ms=$mscale 'BEGIN{vs=sqrt(G*ms/rs)} {OFMT="%.15g"; print $1*ms,$2*rs,$3*rs,$4*rs,$5*vs,$6*vs,$7*vs}' $fname.off__ >$fout.scale__
    mscale=1.0 # use for scaling from Petar unit to stellar evolution unit, since now two units are same, set mscale to 1.0
elif [ $convert == 1 ]; then
    [ $vscale == 'kms2pcmyr' ] && vscale=1.022712165045695
    echo 'Unit convert: distance scale: '$rscale';  mass scale: '$mscale';  velocity scale: '$vscale
    awk -v rs=$rscale -v vs=$vscale -v ms=$mscale '{OFMT="%.15g"; print $1*ms,$2*rs,$3*rs,$4*rs,$5*vs,$6*vs,$7*vs}' $fname.off__ >$fout.scale__
    mscale=1.0 # use for scaling from Petar unit to stellar evolution unit, since now two units are same, set mscale to 1.0
else
    mv $fname.off__ $fout.scale__
fi
rm -f $fname.off__

if [[ $seflag != 'no' ]]; then
    if [[ $seflag == 'base' ]]; then
	echo "Stellar radius (0): " $radius
	awk -v n=$n  'BEGIN{print 0,n,0} {OFMT="%.15g"; print $LINE,0,'$radius',0,0,0,0,NR-ig,0,0,0,0,0,0,0,0,0,0}' $fout.scale__ >$fout
    elif [[ $seflag == 'bse' ]]; then
	echo 'mass scale from PeTar unit (PT) to Msun (m[Msun] = m[PT]*mscale): ' $mscale
	awk -v n=$n -v ms=$mscale  'BEGIN{print 0,n,0} {OFMT="%.15g"; print $LINE, 0,0,0,0,0, 1,$1*ms,$1*ms,0.0,0.0,0.0,0.0,0.0,0.0,0.0, 0.0,NR-ig,0,0,0,0,0,0,0,0,0,0}' $fout.scale__ >$fout
    else
	echo 'Error: unknown option for stellar evolution: '$seflag
    fi
else
    awk -v n=$n 'BEGIN{print 0,n,0} {OFMT="%.15g"; print $LINE, 0,0,NR-ig,0,0,0,0,0,0,0,0,0,0}' $fout.scale__ >$fout
fi
rm -f $fout.scale__
