#version 400 core

layout(location = 0) in vec4 vPosition;
layout(location = 1) in vec4 vColors;

out vec4 v2fcolor;

void main() {
    gl_Position = vPosition;
    v2fcolor = vColors;
}