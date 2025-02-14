import pygame
import moderngl
import numpy as np
from pyrr import Matrix44, Quaternion
from pywavefront import Wavefront

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.DOUBLEBUF | pygame.OPENGL)
pygame.display.set_caption("3D World with ModernGL")

# ModernGL context
ctx = moderngl.create_context()

# Enable depth testing
ctx.enable(moderngl.DEPTH_TEST)

# Load the .obj file
obj = Wavefront("objects/letter/letter_w.obj", collect_faces=True)

# Extract vertices from the .obj file
vertices = np.array(obj.vertices, dtype="f4")

# Create a vertex buffer object (VBO)
vbo = ctx.buffer(vertices.tobytes())

# Shader Program
vertex_shader = """
#version 330
in vec3 in_vert;
uniform mat4 mvp;
void main() {
    gl_Position = mvp * vec4(in_vert, 1.0);
}
"""

fragment_shader = """
#version 330
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);  // White color
}
"""

# Compile shaders and create a program
prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

# Create a vertex array object (VAO)
vao = ctx.simple_vertex_array(prog, vbo, "in_vert")

# Camera and Projection setup
aspect_ratio = screen.get_width() / screen.get_height()
projection = Matrix44.perspective_projection(45.0, aspect_ratio, 0.1, 100.0)
camera_pos = Matrix44.from_translation([0.0, 0.0, -5.0])  # Initial camera position
view = Matrix44.look_at(
    (0.0, 0.0, -5.0),  # Eye position (camera)
    (0.0, 0.0, 0.0),   # Look at the origin
    (0.0, 1.0, 0.0)    # Up direction
)

model = Matrix44.identity()

# Scale the object to make it fit the view
scale_matrix = Matrix44.from_scale([1.0, 1.0, 1.0])  # Adjust scale if necessary

# Create rotation (example: rotating around Y-axis)
axis = np.array([0.0, 1.0, 0.0])  # Y-axis
angle = 0.02  # Small rotation on Y-axis
sin_half_angle = np.sin(angle / 2.0)
cos_half_angle = np.cos(angle / 2.0)

# Creating the quaternion manually
rotation = Quaternion([cos_half_angle, axis[0] * sin_half_angle, axis[1] * sin_half_angle, axis[2] * sin_half_angle])

# Movement speed
movement_speed = 0.1
rotation_speed = 0.02

# Main Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Movement controls (WASD)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        camera_pos = Matrix44.from_translation([0.0, 0.0, camera_pos[3][2] + movement_speed])
    if keys[pygame.K_s]:
        camera_pos = Matrix44.from_translation([0.0, 0.0, camera_pos[3][2] - movement_speed])
    if keys[pygame.K_a]:
        camera_pos = Matrix44.from_translation([camera_pos[3][0] - movement_speed, 0.0, camera_pos[3][2]])
    if keys[pygame.K_d]:
        camera_pos = Matrix44.from_translation([camera_pos[3][0] + movement_speed, 0.0, camera_pos[3][2]])

    # Rotation controls (Arrow keys or mouse)
    if keys[pygame.K_LEFT]:
        rotation = Quaternion([cos_half_angle, 0.0, 1.0 * sin_half_angle, 0.0]) * rotation
    if keys[pygame.K_RIGHT]:
        rotation = Quaternion([cos_half_angle, 0.0, -1.0 * sin_half_angle, 0.0]) * rotation
    if keys[pygame.K_UP]:
        rotation = Quaternion([cos_half_angle, 1.0 * sin_half_angle, 0.0, 0.0]) * rotation
    if keys[pygame.K_DOWN]:
        rotation = Quaternion([cos_half_angle, -1.0 * sin_half_angle, 0.0, 0.0]) * rotation

    # Clear the screen
    ctx.clear(0.1, 0.1, 0.1)  # Dark gray background

    # Apply rotation and scale to model matrix
    model = rotation * model
    model = scale_matrix * model  # Apply scaling to model

    # Update the model-view-projection matrix
    mvp = projection * view * model
    prog["mvp"].write(mvp.astype("f4").tobytes())

    # Render the object
    vao.render()

    # Update the display
    pygame.display.flip()

# Cleanup
pygame.quit()
