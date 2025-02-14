package com.example;

import org.joml.Math;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import static org.lwjgl.glfw.Callbacks.glfwFreeCallbacks;
import static org.lwjgl.glfw.GLFW.GLFW_CONTEXT_VERSION_MAJOR;
import static org.lwjgl.glfw.GLFW.GLFW_CONTEXT_VERSION_MINOR;
import static org.lwjgl.glfw.GLFW.GLFW_KEY_ESCAPE;
import static org.lwjgl.glfw.GLFW.GLFW_KEY_LEFT;
import static org.lwjgl.glfw.GLFW.GLFW_KEY_RIGHT;
import static org.lwjgl.glfw.GLFW.GLFW_OPENGL_CORE_PROFILE;
import static org.lwjgl.glfw.GLFW.GLFW_OPENGL_PROFILE;
import static org.lwjgl.glfw.GLFW.GLFW_PRESS;
import static org.lwjgl.glfw.GLFW.GLFW_RELEASE;
import static org.lwjgl.glfw.GLFW.glfwCreateWindow;
import static org.lwjgl.glfw.GLFW.glfwDestroyWindow;
import static org.lwjgl.glfw.GLFW.glfwInit;
import static org.lwjgl.glfw.GLFW.glfwMakeContextCurrent;
import static org.lwjgl.glfw.GLFW.glfwPollEvents;
import static org.lwjgl.glfw.GLFW.glfwSetKeyCallback;
import static org.lwjgl.glfw.GLFW.glfwSetWindowShouldClose;
import static org.lwjgl.glfw.GLFW.glfwShowWindow;
import static org.lwjgl.glfw.GLFW.glfwSwapBuffers;
import static org.lwjgl.glfw.GLFW.glfwSwapInterval;
import static org.lwjgl.glfw.GLFW.glfwTerminate;
import static org.lwjgl.glfw.GLFW.glfwWindowHint;
import static org.lwjgl.glfw.GLFW.glfwWindowShouldClose;
import org.lwjgl.opengl.GL;
import static org.lwjgl.opengl.GL11.GL_COLOR_BUFFER_BIT;
import static org.lwjgl.opengl.GL11.GL_DEPTH_BUFFER_BIT;
import static org.lwjgl.opengl.GL11.GL_DEPTH_TEST;
import static org.lwjgl.opengl.GL11.GL_FALSE;
import static org.lwjgl.opengl.GL11.GL_FLOAT;
import static org.lwjgl.opengl.GL11.GL_TRIANGLES;
import static org.lwjgl.opengl.GL11.GL_UNSIGNED_INT;
import static org.lwjgl.opengl.GL11.glClear;
import static org.lwjgl.opengl.GL11.glDrawElements;
import static org.lwjgl.opengl.GL11.glEnable;
import static org.lwjgl.opengl.GL15.GL_ARRAY_BUFFER;
import static org.lwjgl.opengl.GL15.GL_ELEMENT_ARRAY_BUFFER;
import static org.lwjgl.opengl.GL15.GL_STATIC_DRAW;
import static org.lwjgl.opengl.GL15.glBindBuffer;
import static org.lwjgl.opengl.GL15.glBufferData;
import static org.lwjgl.opengl.GL15.glGenBuffers;
import static org.lwjgl.opengl.GL20.GL_COMPILE_STATUS;
import static org.lwjgl.opengl.GL20.GL_FRAGMENT_SHADER;
import static org.lwjgl.opengl.GL20.GL_LINK_STATUS;
import static org.lwjgl.opengl.GL20.GL_VERTEX_SHADER;
import static org.lwjgl.opengl.GL20.glAttachShader;
import static org.lwjgl.opengl.GL20.glCompileShader;
import static org.lwjgl.opengl.GL20.glCreateProgram;
import static org.lwjgl.opengl.GL20.glCreateShader;
import static org.lwjgl.opengl.GL20.glDeleteProgram;
import static org.lwjgl.opengl.GL20.glDeleteShader;
import static org.lwjgl.opengl.GL20.glEnableVertexAttribArray;
import static org.lwjgl.opengl.GL20.glGetProgramInfoLog;
import static org.lwjgl.opengl.GL20.glGetProgrami;
import static org.lwjgl.opengl.GL20.glGetShaderInfoLog;
import static org.lwjgl.opengl.GL20.glGetShaderi;
import static org.lwjgl.opengl.GL20.glGetUniformLocation;
import static org.lwjgl.opengl.GL20.glLinkProgram;
import static org.lwjgl.opengl.GL20.glShaderSource;
import static org.lwjgl.opengl.GL20.glUniformMatrix4fv;
import static org.lwjgl.opengl.GL20.glUseProgram;
import static org.lwjgl.opengl.GL20.glVertexAttribPointer;
import static org.lwjgl.opengl.GL30.glBindVertexArray;
import static org.lwjgl.opengl.GL30.glDeleteVertexArrays;
import static org.lwjgl.opengl.GL30.glGenVertexArrays;
import static org.lwjgl.system.MemoryUtil.NULL;

public class Pyramid3D {
    private long window;
    private int width = 800;
    private int height = 600;

    private int vao;
    private int shaderProgram;

    private float rotationAngle = 0.0f;
    private float radius = 5.0f;

    public static void main(String[] args) {
        new Pyramid3D().run();
    }

    public void run() {
        init();
        loop();
        cleanup();
    }

    private void init() {
        // Initialize GLFW
        if (!glfwInit()) {
            throw new IllegalStateException("Unable to initialize GLFW");
        }

        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

        window = glfwCreateWindow(width, height, "3D Pyramid", NULL, NULL);
        if (window == NULL) {
            throw new RuntimeException("Failed to create the GLFW window");
        }

        glfwMakeContextCurrent(window);
        glfwSwapInterval(1); // Enable V-Sync
        glfwShowWindow(window);

        GL.createCapabilities();

        glEnable(GL_DEPTH_TEST);

        // Setup shaders and VAO
        shaderProgram = createShaderProgram();
        vao = createVAO();

        // Set input callbacks
        setupInputCallbacks();
    }

    private void setupInputCallbacks() {
        glfwSetKeyCallback(window, (windowHandle, key, scancode, action, mods) -> {
            if (key == GLFW_KEY_ESCAPE && action == GLFW_PRESS) {
                glfwSetWindowShouldClose(windowHandle, true);
            }
            if (key == GLFW_KEY_LEFT && action != GLFW_RELEASE) {
                rotationAngle -= 2.0f;
            }
            if (key == GLFW_KEY_RIGHT && action != GLFW_RELEASE) {
                rotationAngle += 2.0f;
            }
        });
    }

    private void loop() {
        // Projection matrix
        Matrix4f projection = new Matrix4f().perspective(
                (float) Math.toRadians(45.0),
                (float) width / height,
                0.1f,
                100.0f
        );

        while (!glfwWindowShouldClose(window)) {
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

            // Camera position
            float camX = (float) (radius * Math.sin(Math.toRadians(rotationAngle)));
            float camZ = (float) (radius * Math.cos(Math.toRadians(rotationAngle)));
            Matrix4f view = new Matrix4f().lookAt(
                    new Vector3f(camX, 2.0f, camZ), // Camera position
                    new Vector3f(0.0f, 0.0f, 0.0f), // Target
                    new Vector3f(0.0f, 1.0f, 0.0f)  // Up direction
            );

            // View-projection matrix
            Matrix4f viewProjection = new Matrix4f();
            projection.mul(view, viewProjection);

            // Send the matrix to the shader
            int viewProjectionLoc = glGetUniformLocation(shaderProgram, "viewProjection");
            glUniformMatrix4fv(viewProjectionLoc, false, viewProjection.get(new float[16]));

            // Render the pyramid
            glUseProgram(shaderProgram);
            glBindVertexArray(vao);
            glDrawElements(GL_TRIANGLES, 18, GL_UNSIGNED_INT, 0);

            glfwSwapBuffers(window);
            glfwPollEvents();
        }
    }

    private int createVAO() {
        // Vertex data for a pyramid
        float[] vertices = {
                // Base
                -0.5f, 0.0f, -0.5f,
                 0.5f, 0.0f, -0.5f,
                 0.5f, 0.0f,  0.5f,
                -0.5f, 0.0f,  0.5f,
                // Apex
                 0.0f, 1.0f,  0.0f
        };

        int[] indices = {
                // Base
                0, 1, 2,
                2, 3, 0,
                // Sides
                0, 1, 4,
                1, 2, 4,
                2, 3, 4,
                3, 0, 4
        };

        int vao = glGenVertexArrays();
        int vbo = glGenBuffers();
        int ebo = glGenBuffers();

        glBindVertexArray(vao);

        // Vertex buffer
        glBindBuffer(GL_ARRAY_BUFFER, vbo);
        glBufferData(GL_ARRAY_BUFFER, vertices, GL_STATIC_DRAW);

        // Element buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices, GL_STATIC_DRAW);

        // Vertex attributes
        glVertexAttribPointer(0, 3, GL_FLOAT, false, 3 * Float.BYTES, 0);
        glEnableVertexAttribArray(0);

        return vao;
    }

    private int createShaderProgram() {
        String vertexShaderSource = "#version 330 core\n" +
            "layout (location = 0) in vec3 position;\n" +
            "uniform mat4 viewProjection;\n" +
            "void main() {\n" +
            "    gl_Position = viewProjection * vec4(position, 1.0);\n" +
            "}";

        String fragmentShaderSource = "#version 330 core\n" +
            "out vec4 FragColor;\n" +
            "\n" +
            "void main() {\n" +
            "    FragColor = vec4(1.0, 0.5, 0.2, 1.0);\n" +
            "}";

        int vertexShader = compileShader(GL_VERTEX_SHADER, vertexShaderSource);
        int fragmentShader = compileShader(GL_FRAGMENT_SHADER, fragmentShaderSource);

        int program = glCreateProgram();
        glAttachShader(program, vertexShader);
        glAttachShader(program, fragmentShader);
        glLinkProgram(program);

        if (glGetProgrami(program, GL_LINK_STATUS) == GL_FALSE) {
            throw new RuntimeException("Shader program linking failed: " + glGetProgramInfoLog(program));
        }

        glDeleteShader(vertexShader);
        glDeleteShader(fragmentShader);

        return program;
    }

    private int compileShader(int type, String source) {
        int shader = glCreateShader(type);
        glShaderSource(shader, source);
        glCompileShader(shader);

        if (glGetShaderi(shader, GL_COMPILE_STATUS) == GL_FALSE) {
            throw new RuntimeException("Shader compilation failed: " + glGetShaderInfoLog(shader));
        }

        return shader;
    }

    private void cleanup() {
        glDeleteVertexArrays(vao);
        glDeleteProgram(shaderProgram);
        glfwFreeCallbacks(window);
        glfwDestroyWindow(window);
        glfwTerminate();
    }
}
