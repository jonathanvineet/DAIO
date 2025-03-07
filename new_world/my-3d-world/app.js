// Create the scene
const scene = new THREE.Scene();

// Create the camera
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

// Create the renderer and set the size
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Set up lighting
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(10, 10, 10).normalize();
scene.add(light);

// Add ambient light for better visibility
const ambientLight = new THREE.AmbientLight(0x404040); // Soft white light
scene.add(ambientLight);

// Load the .obj file
const loader = new THREE.OBJLoader();
loader.load('E:/Vineet_Ideas/DAIO/new_world/objects/letter/letter_w.obj', function (obj) {
  scene.add(obj);
  obj.position.set(0, 0, 0); // Position the object
  obj.scale.set(2, 2, 2); // Adjust the scale to make it visible if it's too small
  obj.castShadow = true; // Enable shadows for this object
  obj.receiveShadow = true;
});

// Set the camera position
camera.position.z = 10; // Adjust the camera position to frame the model

// Add mouse controls for camera movement (orbit controls)
const controls = new THREE.OrbitControls(camera, renderer.domElement);

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  controls.update(); // Update the controls
  renderer.render(scene, camera);
}

// Start the animation loop
animate();
