// Setup canvas
var canvas = document.getElementById("image");
var ctx = canvas.getContext("2d");

// Load image
var image = new Image();
image.crossOrigin = "anonymous";
image.src = "img/real2.jpg";

// Setup MatterJS
var Engine = Matter.Engine,
	Render = Matter.Render,
	World = Matter.World,
	Bodies = Matter.Bodies,
	MouseConstraint = Matter.MouseConstraint,
	Mouse = Matter.Mouse,
	Events = Matter.Events,
	Body = Matter.Body;

// Leap motion
var leapCursor;

// Main Variables
var engine;
var render;
var renderCanvas;
var mConstraint;
var mouse;
var mouseBox;
var SOUNDS;
var minSpawnX;
var maxSpawnX;

// Constants
const MAX_HEALTH = 3;
const MIN_HEALTH = 1;
const SCALE = 3;
const deathAreaOffset = 2;

function initMatter() {
	// Setup preview canvas
	ctx.canvas.width = image.width;
	ctx.canvas.height = image.height;
	ctx.drawImage(image,0,0);

	// Create engine & renderer
	engine = Engine.create();

	renderCanvas = document.getElementById("render");

	render = Render.create({
		engine: engine,
		canvas: renderCanvas,
		options: {
			width: image.width*SCALE,
			height: image.height*SCALE,
			showVelocity: false,
			wireframes: false
		}
	});
	renderCanvas.getContext("2d").scale(SCALE,SCALE);

	Render.run(render);
	Engine.run(engine);

	// Create mouse & constraints
	mouseBox = Bodies.rectangle(300, 100, 40, 40, {
		label: "weapon",
		render: {
			fillStyle: "green",
			lineWidth: 0
		}
	});

	mouse = Mouse.create(renderCanvas);
	mouse.pixelRatio = SCALE;
	mConstraint = MouseConstraint.create(engine, {
		mouse: mouse,
		constraint: {
		    render: {
		      visible: false
			}
		}
	});

	World.add(engine.world, mouseBox);
	World.add(engine.world, mConstraint);

	// Main collision handler
	Events.on(engine, 'collisionStart', matterCollision);
}
function initLeap() {
	leapCursor = Bodies.rectangle(100,100, 10,10, {
		isStatic: true,
		label: "leap",
		mass: 10,
		render: {
			fillStyle: "purple",
			lineWidth: 2
		},
		collisionFilter: {
			mask: 0x0002
		}
	});
	World.add(engine.world, leapCursor);
}
function initSounds() {
	SOUNDS = document.getElementsByClassName("sounds");
}
function playSound(_name, _volume) {
	for( var i = 0; i < SOUNDS.length; i++ ) {
		if( SOUNDS[i].id == _name ) {
			SOUNDS[i].volume = _volume;
			SOUNDS[i].play();
			return;
		}
	}
}
function choose(_list) {
	var num = Math.round(Math.random()*_list.length);
	return _list[num];
}
function matterCollision(e) {
    var pairs = e.pairs;

    // change object colours to show those starting a collision
    for (var i = 0; i < pairs.length; i++) {
        var pair = pairs[i];
        
        // ENEMY COLLISIONS
        if( pair.bodyB.label.substring(0, 5) == "enemy" ) {
        	// With side death walls
        	if( pair.bodyA.label == "death" ) {
        		pair.bodyB.render.fillStyle = '#333';
        		World.remove(engine.world, pair.bodyB);
        	}
        	// With player weapon
        	if( pair.bodyA.label == "weapon" ) {
	        	var health = pair.bodyB.label.substring(5, pair.bodyB.label.length) - 1;
	        	pair.bodyB.render.sprite.texture = "img/enemy1_hurt.png";
	        	pair.bodyB.label = "enemy" + health;

	        	if( health <= 0 ) {
					World.remove(engine.world, pair.bodyB);
	        		playSound(choose(["bap1", "bap2", "bap3", "bap4"]), 1);
	        	}
	        	else
	        		playSound(choose(["squish", "pop"]), 0.5);
        	}
        	// With ground (solid objects)
        	if( pair.bodyA.label == "rlobj" ) {
        		pair.bodyB.frictionAir = 0.1;
        	}
        }
    }
}
function analyseImage() {
	var pix = ctx.getImageData(0,0,image.width,image.height).data;
	var solid = 0;
	var startX = 0;
	var startY = 0;

	for( i = 0; i < pix.length; i+=4 ) {
		var ni = Math.round(i/4);
		var x = Math.round( ni % image.width );
		var y = Math.round( ni / image.width );

		// Convert to HSL and check if it's solid
		var hs = rgbToHsl(pix[i], pix[i+1], pix[i+2]);

		// End platform if we move to the next row
		if( solid != 0 && y != startY ) {
			endPlatform(startX, startY, solid);
			solid = 0;
		}

		if( hs[2] <= 0.4 ) {
			// Check if it's the first in the platform
			if( solid == 0 ) {
				startX = x;
				startY = y;
			}
			solid += 1;
		}
		// End the platform if its no longer solid, or we change rows
		else if( solid != 0 ) {
			endPlatform(startX, startY, solid);
			solid = 0;
		}
	} // End FOR


	// Find and create boundaries
	var checks = [
		{x: image.width/2, y: 50}, {x: 0, y: 50}, false, // left
		{x: image.width/2, y: 50}, {x: image.width, y: 50}, true, // right
	];
	
	for( var c = 0; c < checks.length; c += 3 ) {
		// Send a ray out to find nearest point
		var objects = Matter.Query.ray(engine.world.bodies,
			checks[c],
			checks[c+1], 50);

		var invert = checks[c+2];
		var max_val = image.width*invert;

		// Find the point sticking out the most
		if( objects.length > 0 ) {
			for( var i = 0; i < objects.length; i++ ) {
				// Check if we've found a higher value
				if( invert == false ) { // left
					var px = objects[i].bodyA.position.x + objects[i].bodyA.area/2;
					if( px > max_val ) { max_val = px; }
				}
				else {
					var px = objects[i].bodyA.position.x - objects[i].bodyA.area/2;
					if( px < max_val ) { max_val = px; }
				}

				objects[i].bodyA.render.fillStyle = "green";
			}
		}

		// Store the min / max for spawning enemies
		if( invert )
			maxSpawnX = max_val;
		else
			minSpawnX = max_val;

		// Create object for side collision
		var pw = Math.abs(max_val-(image.width*invert));
		var px = Math.abs((image.width*invert)-(pw/2));

		var edge = Bodies.rectangle(px, image.height/2, pw, image.height, {
			isStatic: true,
			label: "death",
			render: {
				fillStyle: "blue"
			}
		});
		World.add(engine.world, edge);
	}// End of Checks FOR
}
function endPlatform(_startX, _startY, _solid) {
	ctx.fillRect(_startX, _startY, _solid, 1);
	var platform = Bodies.rectangle(_startX+(_solid/2), _startY, _solid, 1, {
		isStatic: true,
		label: "rlobj",
		render: {
			fillStyle: "red",
			lineWidth: 0
		}
	});
	World.add(engine.world, platform);
}
function rgbToHsl(r, g, b){
	r /= 255, g /= 255, b /= 255;
  var max = Math.max(r, g, b), min = Math.min(r, g, b);
  var h, s, l = (max + min) / 2;
  
	if(max == min){
	  h = s = 0; // achromatic
	} else {
    var d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
		switch(max){
			case r: h = (g - b) / d + (g < b ? 6 : 0); break;
			case g: h = (b - r) / d + 2; break;
			case b: h = (r - g) / d + 4; break;
		}

		h /= 6;
	}
  return [h, s, l];
}

image.onload = function() {
	// Page has finished loading, start loading the game
	initMatter();
	initLeap();
	initSounds();
	analyseImage();
}
Leap.loop({hand: function(_hand) {
	var screenPosition = _hand.screenPosition(_hand.palmPosition);
	// screenPosition - 0 = x, 1 = y, 2 = z, .toPrecision
	// _hand.pinchStrength
	var sx = screenPosition[0]-600;
	var sy = screenPosition[1]+400;

	Body.setPosition(mouseBox, {x: sx, y: sy});
	Body.setPosition(leapCursor, {x: sx, y: sy});
}})
.use('screenPosition', {
	scale: 1
});
setInterval(function() {
	var health = Math.round(Math.random()*MAX_HEALTH)+MIN_HEALTH;
	var spawnx = Math.round(Math.random()*maxSpawnX)+minSpawnX;

	var item = Bodies.circle(spawnx, 20, 10, {
		mass: 0.5,
		frictionAir: 1.0,
		label: "enemy" + health,
		collisionFilter: {
			category: 0x0001
		},
		render: {
            sprite: {
                texture: 'img/enemy1.png',
                xScale: 0.1,
                yScale: 0.1
            }
        }
	});
	World.add(engine.world, item);
}, 3000);
