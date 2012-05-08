/*
  --- menu level scope settins structure --- 
  note that this structure has changed its format since previous version.
  Now this structure has the same layout as Tigra Menu GOLD.
  Format description can be found in product documentation.
*/
var MENU_POS = [
{
	// item sizes
	'height': 26,
	'width': [60,150,80,90,70,70],
	'subwidth': [160,180,185,190,170,190,100,100],
	//'width': [150,200,150,100,90],
	// menu block offset from the origin:
	//	for root level origin is upper left corner of the page
	//	for other levels origin is upper left corner of parent item
	'block_top': 117,
	'block_left': 26,
	// offsets between items of the same level
	'top': 0,
	'left': [null,60,150,80,90,70,70],
	//'left': [100,150,200,150,100,90],
	// time in milliseconds before menu is hidden after cursor has gone out
	// of any items
	'hide_delay': 200,
	'expd_delay': 200,
	'css' : {
		'outer': ['m0l0oout', 'm0l0oover'],
		'inner': ['m0l0iout', 'm0l0iover']
	}
},
{
	'height': 29,
	'width': 200,
	'subwidth': [],
	'block_top': 15,
	'block_left': 5,
	'top': 28,
	'left': 0,
	'css': {
		'outer' : ['m0l1oout', 'm0l1oover'],
		'inner' : ['m0l1iout', 'm0l1iover']
	}
},
{
	'height': 29,
	'width': 150,
	'subwidth': [],
	'block_top': 15,
	'block_left': 175,
	'css': {
		'outer': ['m0l2oout', 'm0l2oover'],
		'inner': ['m0l2iout', 'm0l2iover']
	}
},
{
	'height': 29,
	'width': 150,
	'subwidth': [],
	'block_top': 15,
	'block_left': 145,
	'css': {
		'outer': ['m0l3oout', 'm0l3oover'],
		'inner': ['m0l3iout', 'm0l3iover']
	}
},
{
	'height': 29,
	'width': 350,
	'subwidth': [],
	'block_top': 15,
	'block_left': 145,
	'css': {
		'outer': ['m0l4oout', 'm0l4oover'],
		'inner': ['m0l4iout', 'm0l4iover']
	}
},
{
	'height': 29,
	'width': 350,
	'subwidth': [],
	'block_top': 15,
	'block_left': 175,
	'css': {
		'outer': ['m0l5oout', 'm0l5oover'],
		'inner': ['m0l5iout', 'm0l5iover']
	}
}
]
