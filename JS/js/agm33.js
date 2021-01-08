// Setup canvas
var canvas = document.getElementById("image");
var ctx = canvas.getContext("2d");

// Load image
var image = new Image();
image.crossOrigin = "anonymous";
image.src = "real2.jpg";

// Setup MatterJS
var Engine = Matter.Engine,
	Render = Matter.Render,
	World = Matter.World,
	Bodies = Matter.Bodies,
	MouseConstraint = Matter.MouseConstraint,
	Mouse = Matter.Mouse,
	Events = Matter.Events,
	Body = Matter.Body;

// Main Variables
var engine;
var render;
var renderCanvas;
var mConstraint;
var mouse;
var mouseBox;
const SCALE = 3;

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
			showVelocity: true,
			wireframes: false
		}
	});
	renderCanvas.getContext("2d").scale(SCALE,SCALE);

	Render.run(render);
	Engine.run(engine);

	// Create mouse & constraints
	mouseBox = Bodies.rectangle(300, 20, 20, 20, {
		render: {
			fillStyle: "green",
			lineWidth: 0
		}
	});

	mouse = Mouse.create(renderCanvas);
	mouse.pixelRatio = SCALE;
	mConstraint = MouseConstraint.create(engine, {
		mouse: mouse
	});

	World.add(engine.world, mouseBox);
	World.add(engine.world, mConstraint);

	for (var i = 0; i < 10; i++) {
		var item = Bodies.circle(300, 20, 10);
		World.add(engine.world, item);
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
}
function endPlatform(_startX, _startY, _solid) {
	ctx.fillRect(_startX, _startY, _solid, 1);
	var platform = Bodies.rectangle(_startX+(_solid/2), _startY, _solid, 1, {
		isStatic: true,
		render: {
			fillStyle: "red",
			lineWidth: 0
		}
	});
	World.add(engine.world, platform);
}


image.onload = function() {
	initMatter();
	analyseImage();
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

