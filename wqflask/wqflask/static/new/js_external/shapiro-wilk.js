/*
 *  Ported from http://svn.r-project.org/R/trunk/src/library/stats/src/swilk.c
 *
 *  R : A Computer Language for Statistical Data Analysis
 *  Copyright (C) 2000-12   The R Core Team.
 *
 *  Based on Applied Statistics algorithms AS181, R94
 *    (C) Royal Statistical Society 1982, 1995
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, a copy is available at
 *  http://www.r-project.org/Licenses/
 */

function sign(x) {
    if (x == 0)
        return 0;
    return x > 0 ? 1 : -1;
}

function ShapiroWilkW(x)
{
    function poly(cc, nord, x)
    {
        /* Algorithm AS 181.2	Appl. Statist.	(1982) Vol. 31, No. 2
        Calculates the algebraic polynomial of order nord-1 with array of coefficients cc.
        Zero order coefficient is cc(1) = cc[0] */
        var p;
        var ret_val;

        ret_val = cc[0];
        if (nord > 1) {
    	    p = x * cc[nord-1];
    	    for (j = nord - 2; j > 0; j--)
    	        p = (p + cc[j]) * x;
    	    ret_val += p;
        }
        return ret_val;
    }
    x = x.sort(function (a, b) { return a - b; });
    var n = x.length;
    if (n < 3)
        return undefined;
    var nn2 = Math.floor(n / 2);
    var a = new Array(Math.floor(nn2) + 1); /* 1-based */

/*	ALGORITHM AS R94 APPL. STATIST. (1995) vol.44, no.4, 547-551.

	Calculates the Shapiro-Wilk W test and its significance level
*/
    var small = 1e-19;

    /* polynomial coefficients */
    var g = [ -2.273, 0.459 ];
    var c1 = [ 0, 0.221157, -0.147981, -2.07119, 4.434685, -2.706056 ];
    var c2 = [ 0, 0.042981, -0.293762, -1.752461, 5.682633, -3.582633 ];
    var c3 = [ 0.544, -0.39978, 0.025054, -6.714e-4 ];
    var c4 = [ 1.3822, -0.77857, 0.062767, -0.0020322 ];
    var c5 = [ -1.5861, -0.31082, -0.083751, 0.0038915 ];
    var c6 = [ -0.4803, -0.082676, 0.0030302 ];

    /* Local variables */
    var i, j, i1;

    var ssassx, summ2, ssumm2, gamma, range;
    var a1, a2, an, m, s, sa, xi, sx, xx, y, w1;
    var fac, asa, an25, ssa, sax, rsn, ssx, xsx;

    var pw = 1;
    an = n;

    if (n == 3)
        a[1] = 0.70710678;/* = sqrt(1/2) */
    else {
	    an25 = an + 0.25;
        summ2 = 0.0;
	    for (i = 1; i <= nn2; i++) {
            a[i] = jStat.normal.inv((i - 0.375) / an25, 0, 1); // p(X <= x),
            var r__1 = a[i];
            summ2 += r__1 * r__1;
	    }
    	summ2 *= 2;
    	ssumm2 = Math.sqrt(summ2);
    	rsn = 1 / Math.sqrt(an);
    	a1 = poly(c1, 6, rsn) - a[1] / ssumm2;

    	/* Normalize a[] */
    	if (n > 5) {
            i1 = 3;
            a2 = -a[2] / ssumm2 + poly(c2, 6, rsn);
            fac = Math.sqrt((summ2 - 2 * (a[1] * a[1]) - 2 * (a[2] * a[2])) / (1 - 2 * (a1 * a1) - 2 * (a2 * a2)));
            a[2] = a2;
        } else {
            i1 = 2;
            fac = Math.sqrt((summ2 - 2 * (a[1] * a[1])) / ( 1  - 2 * (a1 * a1)));
    	}
        a[1] = a1;
        for (i = i1; i <= nn2; i++)
            a[i] /= - fac;
    }

/*	Check for zero range */

    range = x[n - 1] - x[0];
    if (range < small) {
        console.log('range is too small!')
        return undefined;
    }


/*	Check for correct sort order on range - scaled X */

    xx = x[0] / range;
    sx = xx;
    sa = -a[1];
    for (i = 1, j = n - 1; i < n; j--) {
	    xi = x[i] / range;
        if (xx - xi > small) {
            console.log("xx - xi is too big.", xx - xi);
            return undefined;
        }
	    sx += xi;
	    i++;
	    if (i != j)
	        sa += sign(i - j) * a[Math.min(i, j)];
	    xx = xi;
    }
    if (n > 5000) {
        console.log("n is too big!")
        return undefined;
    }


/*	Calculate W statistic as squared correlation
	between data and coefficients */

    sa /= n;
    sx /= n;
    ssa = ssx = sax = 0.;
    for (i = 0, j = n - 1; i < n; i++, j--) {
	    if (i != j)
	        asa = sign(i - j) * a[1 + Math.min(i, j)] - sa;
	    else
	        asa = -sa;
	    xsx = x[i] / range - sx;
	    ssa += asa * asa;
	    ssx += xsx * xsx;
	    sax += asa * xsx;
    }

/*	W1 equals (1-W) calculated to avoid excessive rounding error
	for W very near 1 (a potential problem in very large samples) */

    ssassx = Math.sqrt(ssa * ssx);
    w1 = (ssassx - sax) * (ssassx + sax) / (ssa * ssx);
    var w = 1 - w1;

/*	Calculate significance level for W */

    if (n == 3) {/* exact P value : */
	    var pi6 = 1.90985931710274; /* = 6/pi */ 
	    var stqr = 1.04719755119660; /* = asin(sqrt(3/4)) */
	    pw = pi6 * (Math.asin(Math.sqrt(w)) - stqr);
        if (pw < 0.)
            pw = 0;
	    return w;
    }
    y = Math.log(w1);
    xx = Math.log(an);
    if (n <= 11) {
	    gamma = poly(g, 2, an);
	    if (y >= gamma) {
	        pw = 1e-99; /* an "obvious" value, was 'small' which was 1e-19f */
	        return w;
	    }
	    y = -Math.log(gamma - y);
	    m = poly(c3, 4, an);
	    s = Math.exp(poly(c4, 4, an));
    } else { /* n >= 12 */
	    m = poly(c5, 4, xx);
	    s = Math.exp(poly(c6, 3, xx));
    }

    pw = 0.5 - 0.5 * jStat.erf((y - m) / Math.sqrt(2) / s)

    return {w: w, p: pw};
}
