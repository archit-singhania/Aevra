#version 460 core

precision highp float;

uniform vec2 uSize;
uniform float uTime;

out vec4 fragColor;

// Ashima/McEwan simplex noise (2D), condensed for a cheap mobile-friendly cost.
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
  m = m * m;
  m = m * m;
  vec3 x = 2.0 * fract(p * 0.024390243902439) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vec2 fragCoord = FlutterFragCoord().xy;
  vec2 uv = fragCoord / uSize;
  vec2 aspectUv = (uv - 0.5) * vec2(uSize.x / uSize.y, 1.0) + 0.5;

  float t = uTime * 0.024;

  float n1 = snoise(aspectUv * 1.3 + t);
  float n2 = snoise(aspectUv * 2.0 + vec2(5.0, -3.0) + t * 1.15);
  float field = n1 * 0.65 + n2 * 0.35;

  vec3 bg = vec3(0.027, 0.035, 0.051);
  vec3 brass = vec3(0.788, 0.643, 0.361);
  vec3 inkEmerald = vec3(0.247, 0.365, 0.322);
  vec3 platinum = vec3(0.722, 0.745, 0.780);

  float brassMask = smoothstep(0.18, 0.62, field) * smoothstep(0.05, 0.55, 1.0 - length(aspectUv - vec2(0.72, 0.28)));
  float emeraldMask = smoothstep(0.15, 0.6, -field + 0.15) * smoothstep(0.05, 0.65, 1.0 - length(aspectUv - vec2(0.22, 0.78)));
  float platinumMask = smoothstep(0.2, 0.58, field * 0.6 + 0.2) * smoothstep(0.05, 0.6, 1.0 - length(aspectUv - vec2(0.5, 0.5)));

  vec3 color = bg;
  color += brass * brassMask * 0.10;
  color += inkEmerald * emeraldMask * 0.09;
  color += platinum * platinumMask * 0.05;

  float vignette = smoothstep(1.05, 0.25, length(aspectUv - 0.5));
  color *= mix(0.75, 1.0, vignette);

  fragColor = vec4(color, 1.0);
}
