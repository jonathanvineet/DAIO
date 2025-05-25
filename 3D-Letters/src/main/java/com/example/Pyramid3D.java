package com.example;

import org.joml.Matrix4f;
import static org.lwjgl.glfw.GLFW.GLFW_CURSOR;
import static org.lwjgl.glfw.GLFW.GLFW_CURSOR_DISABLED;
import static org.lwjgl.glfw.GLFW.GLFW_FALSE;
import static org.lwjgl.glfw.GLFW.GLFW_MOUSE_BUTTON_LEFT;
import static org.lwjgl.glfw.GLFW.GLFW_PRESS;
import static org.lwjgl.glfw.GLFW.GLFW_RESIZABLE;
import static org.lwjgl.glfw.GLFW.GLFW_TRUE;
import static org.lwjgl.glfw.GLFW.GLFW_VISIBLE;
import static org.lwjgl.glfw.GLFW.glfwCreateWindow;
import static org.lwjgl.glfw.GLFW.glfwDefaultWindowHints;
import static org.lwjgl.glfw.GLFW.glfwGetMouseButton;
import static org.lwjgl.glfw.GLFW.glfwInit;
import static org.lwjgl.glfw.GLFW.glfwMakeContextCurrent;
import static org.lwjgl.glfw.GLFW.glfwPollEvents;
import static org.lwjgl.glfw.GLFW.glfwSetCursorPos;
import static org.lwjgl.glfw.GLFW.glfwSetCursorPosCallback;
import static org.lwjgl.glfw.GLFW.glfwSetInputMode;
import static org.lwjgl.glfw.GLFW.glfwShowWindow;
import static org.lwjgl.glfw.GLFW.glfwSwapBuffers;
import static org.lwjgl.glfw.GLFW.glfwSwapInterval;
import static org.lwjgl.glfw.GLFW.glfwTerminate;
import static org.lwjgl.glfw.GLFW.glfwWindowHint;
import static org.lwjgl.glfw.GLFW.glfwWindowShouldClose;
import org.lwjgl.glfw.GLFWErrorCallback;
import org.lwjgl.opengl.GL;
import static org.lwjgl.opengl.GL11.GL_COLOR_BUFFER_BIT;
import static org.lwjgl.opengl.GL11.GL_DEPTH_BUFFER_BIT;
import static org.lwjgl.opengl.GL11.GL_DEPTH_TEST;
import static org.lwjgl.opengl.GL11.GL_LINES;
import static org.lwjgl.opengl.GL11.GL_LINE_LOOP;
import static org.lwjgl.opengl.GL11.GL_MODELVIEW;
import static org.lwjgl.opengl.GL11.GL_PROJECTION;
import static org.lwjgl.opengl.GL11.GL_QUADS;
import static org.lwjgl.opengl.GL11.GL_TRIANGLES;
import static org.lwjgl.opengl.GL11.glBegin;
import static org.lwjgl.opengl.GL11.glClear;
import static org.lwjgl.opengl.GL11.glColor3f;
import static org.lwjgl.opengl.GL11.glEnable;
import static org.lwjgl.opengl.GL11.glEnd;
import static org.lwjgl.opengl.GL11.glLoadIdentity;
import static org.lwjgl.opengl.GL11.glLoadMatrixf;
import static org.lwjgl.opengl.GL11.glMatrixMode;
import static org.lwjgl.opengl.GL11.glPopMatrix;
import static org.lwjgl.opengl.GL11.glPushMatrix;
import static org.lwjgl.opengl.GL11.glScalef;
import static org.lwjgl.opengl.GL11.glTranslatef;
import static org.lwjgl.opengl.GL11.glVertex3f;
import static org.lwjgl.system.MemoryUtil.NULL;

public class Pyramid3D {
    private long window;

    private float cameraX = 0.0f, cameraY = 1.5f, cameraZ = 5.0f;
    private float cameraAngleX = 0.0f, cameraAngleY = 0.0f;
    private float mouseSensitivity = 0.2f;
    private double lastMouseX, lastMouseY;

    private final char[] letters = {'H', 'E', 'L', 'L', 'O'};

    public void run() {
        init();
        loop();
        glfwTerminate();
    }

    private void init() {
        GLFWErrorCallback.createPrint(System.err).set();
        if (!glfwInit()) {
            throw new IllegalStateException("Unable to initialize GLFW");
        }

        glfwDefaultWindowHints();
        glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE);
        glfwWindowHint(GLFW_RESIZABLE, GLFW_TRUE);

        window = glfwCreateWindow(800, 600, "3D Pyramid with Letters", NULL, NULL);
        if (window == NULL) {
            throw new RuntimeException("Failed to create GLFW window");
        }

        glfwMakeContextCurrent(window);
        glfwSwapInterval(1);
        glfwShowWindow(window);

        GL.createCapabilities();

        glEnable(GL_DEPTH_TEST);

        setupMouseCallbacks();
    }

    private void setupMouseCallbacks() {
        glfwSetCursorPosCallback(window, (window, xpos, ypos) -> {
            double deltaX = xpos - lastMouseX;
            double deltaY = ypos - lastMouseY;

            if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS) {
                cameraAngleX += deltaX * mouseSensitivity;
                cameraAngleY -= deltaY * mouseSensitivity;

                cameraAngleY = Math.max(-89.0f, Math.min(89.0f, cameraAngleY));
            }

            lastMouseX = xpos;
            lastMouseY = ypos;
        });

        glfwSetCursorPos(window, 400, 300);
        glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
    }

    private void loop() {
        while (!glfwWindowShouldClose(window)) {
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

            glLoadIdentity();
            setupCamera();

            drawFloor();
            drawPyramid();
            drawLettersNextToPyramid();

            glfwSwapBuffers(window);
            glfwPollEvents();
        }
    }

    private void setupCamera() {
        Matrix4f projection = new Matrix4f().perspective((float) Math.toRadians(70.0f), 800f / 600f, 0.1f, 100.0f);
        Matrix4f view = new Matrix4f().rotate((float) Math.toRadians(cameraAngleY), 1, 0, 0)
                                      .rotate((float) Math.toRadians(cameraAngleX), 0, 1, 0)
                                      .translate(-cameraX, -cameraY, -cameraZ);

        glMatrixMode(GL_PROJECTION);
        glLoadMatrixf(projection.get(new float[16]));
        glMatrixMode(GL_MODELVIEW);
        glLoadMatrixf(view.get(new float[16]));
    }

    private void drawFloor() {
        glColor3f(0.3f, 0.6f, 0.3f);
        glBegin(GL_QUADS);
        glVertex3f(-10.0f, 0.0f, -10.0f);
        glVertex3f(-10.0f, 0.0f, 10.0f);
        glVertex3f(10.0f, 0.0f, 10.0f);
        glVertex3f(10.0f, 0.0f, -10.0f);
        glEnd();
    }

    private void drawPyramid() {
        glBegin(GL_TRIANGLES);

        // Front face
        glColor3f(1.0f, 0.0f, 0.0f);
        glVertex3f(0.0f, 1.0f, 0.0f);
        glVertex3f(-1.0f, 0.0f, 1.0f);
        glVertex3f(1.0f, 0.0f, 1.0f);

        // Right face
        glColor3f(0.0f, 1.0f, 0.0f);
        glVertex3f(0.0f, 1.0f, 0.0f);
        glVertex3f(1.0f, 0.0f, 1.0f);
        glVertex3f(1.0f, 0.0f, -1.0f);

        // Back face
        glColor3f(0.0f, 0.0f, 1.0f);
        glVertex3f(0.0f, 1.0f, 0.0f);
        glVertex3f(1.0f, 0.0f, -1.0f);
        glVertex3f(-1.0f, 0.0f, -1.0f);

        // Left face
        glColor3f(1.0f, 1.0f, 0.0f);
        glVertex3f(0.0f, 1.0f, 0.0f);
        glVertex3f(-1.0f, 0.0f, -1.0f);
        glVertex3f(-1.0f, 0.0f, 1.0f);

        glEnd();
    }

    private void drawLettersNextToPyramid() {
        float startX = 2.5f; // Position the letters clearly beside the pyramid
        float startY = 1.0f;
        float spacing = 1.5f;

        glColor3f(1.0f, 1.0f, 1.0f); // White letters

        for (int i = 0; i < letters.length; i++) {
            char letter = letters[i];
            drawLetter(letter, startX + i * spacing, startY, 0.0f);
        }
    }

    private void drawLetter(char letter, float x, float y, float z) {
        glPushMatrix();
        glTranslatef(x, y, z);
        glScalef(1.0f, 1.0f, 1.0f); // Make the letters larger for visibility

        switch (Character.toUpperCase(letter)) {
            case 'H':
                drawBoldH();
                break;
            case 'E':
                drawBoldE();
                break;
            case 'L':
                drawBoldL();
                break;
            case 'O':
                drawBoldO();
                break;
            default:
                break;
        }

        glPopMatrix();
    }

    private void drawBoldH() {
        for (float offset = -0.05f; offset <= 0.05f; offset += 0.02f) {
            glBegin(GL_LINES);
            glVertex3f(-0.5f + offset, 0.5f, 0.0f);
            glVertex3f(-0.5f + offset, -0.5f, 0.0f);

            glVertex3f(0.5f + offset, 0.5f, 0.0f);
            glVertex3f(0.5f + offset, -0.5f, 0.0f);

            glVertex3f(-0.5f, 0.0f + offset, 0.0f);
            glVertex3f(0.5f, 0.0f + offset, 0.0f);
            glEnd();
        }
    }

    private void drawBoldE() {
        for (float offset = -0.05f; offset <= 0.05f; offset += 0.02f) {
            glBegin(GL_LINES);
            glVertex3f(-0.5f + offset, 0.5f, 0.0f);
            glVertex3f(-0.5f + offset, -0.5f, 0.0f);

            glVertex3f(-0.5f, 0.5f + offset, 0.0f);
            glVertex3f(0.5f, 0.5f + offset, 0.0f);

            glVertex3f(-0.5f, 0.0f + offset, 0.0f);
            glVertex3f(0.3f, 0.0f + offset, 0.0f);

            glVertex3f(-0.5f, -0.5f + offset, 0.0f);
            glVertex3f(0.5f, -0.5f + offset, 0.0f);
            glEnd();
        }
    }

    private void drawBoldL() {
        for (float offset = -0.05f; offset <= 0.05f; offset += 0.02f) {
            glBegin(GL_LINES);
            glVertex3f(-0.5f + offset, 0.5f, 0.0f);
            glVertex3f(-0.5f + offset, -0.5f, 0.0f);

            glVertex3f(-0.5f, -0.5f + offset, 0.0f);
            glVertex3f(0.5f, -0.5f + offset, 0.0f);
            glEnd();
        }
    }

    private void drawBoldO() {
        for (float offset = -0.05f; offset <= 0.05f; offset += 0.02f) {
            glBegin(GL_LINE_LOOP);
            for (int i = 0; i < 360; i += 10) {
                float angle = (float) Math.toRadians(i);
                glVertex3f((float) Math.cos(angle) * 0.5f + offset, (float) Math.sin(angle) * 0.5f, 0.0f);
            }
            glEnd();
        }
    }

    public static void main(String[] args) {
        new Pyramid3D().run();
    }
}



/*
/usr/bin/env /Users/vine/Library/Application\ Support/Code/User/globalStorage/pleiades.java-extension-pack-jdk/java/8/bin/java \
-XstartOnFirstThread \
-Djava.library.path=G:/Vineet_Ideas/DAIO/3D-Letters/lwjgl-release-3.3.6-custom/native/windows \
-cp /var/folders/5k/pq2g97cx76vgrnpw0g3v3_f80000gn/T/cp_ccekbbcd2tu1s5llref3v8lhx.jar \
com.example.Pyramid3D
 */

 /*
 java -XstartOnFirstThread \
    -Dorg.lwjgl.librarypath=target/natives \
    -cp "target/classes:$(find ~/.m2/repository/org/lwjgl ~/.m2/repository/org/joml -name '*.jar' | tr '\n' ':')" \
    com.example.Pyramid3D */