// A 3D head for the x-ray view, drawn with three.js. Illustration only.
//
// The shapes are real anatomy from BodyParts3D (see THIRD_PARTY.md), cut down
// to the head and neck by scripts/build_anatomy.mjs and passed in as
// `A.anatomy`. They are a picture: none of them feeds the model. The only
// things driven by the model are the colour of the two brain zones, the
// brightness and pulse speed of each zone's arteries, the narrowing of the
// carotids and the eyelids (see ASSUMPTIONS.md, A13).
function buildHead3D(THREE, host, A) {
  "use strict";
  const V3 = THREE.Vector3, D = A.anatomy;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const bytes = (text) => Uint8Array.from(atob(text), (c) => c.charCodeAt(0));

  // Unpack one mesh of the anatomy file. Positions are stored as 16-bit steps
  // inside the mesh's own box; `tag` and `value` are one byte per point.
  function unpack(m) {
    const packed = new Uint16Array(bytes(m.positions).buffer), position = new Float32Array(packed.length);
    for (let i = 0; i < packed.length; i++) position[i] = m.low[i % 3] + ((m.high[i % 3] - m.low[i % 3]) * packed[i]) / 65535;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(position, 3));
    const faces = bytes(m.faces).buffer;
    geometry.setIndex(new THREE.BufferAttribute(m.wide ? new Uint32Array(faces) : new Uint16Array(faces), 1));
    geometry.setAttribute("tag", new THREE.BufferAttribute(m.tag ? Float32Array.from(bytes(m.tag)) : new Float32Array(m.points), 1));
    geometry.setAttribute("value", new THREE.BufferAttribute(m.value ? Float32Array.from(bytes(m.value), (v) => (v * m.valueMax) / 255) : new Float32Array(m.points), 1));
    geometry.computeVertexNormals();
    return geometry;
  }

  // ---- materials -------------------------------------------------------------
  const FLOOR = D.meshes.skin.low[1];                 // the cut at the bottom of the neck; everything fades out toward it
  const VERTEX = `
    attribute float tag; attribute float value;
    varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace; varying float vTag; varying float vValue;
    void main() {
      vec4 eye = modelViewMatrix * vec4(position, 1.0);
      vNormal = normalMatrix * normal; vView = -eye.xyz; vPlace = position; vTag = tag; vValue = value;
      gl_Position = projectionMatrix * eye;
    }`;
  const LIGHT = `
    const vec3 KEY = vec3(-0.42, 0.62, 0.66), FILL = vec3(0.62, 0.1, 0.5);      // fixed to the viewer, not to the head
    float fadeOut(float y) { return smoothstep(${FLOOR.toFixed(1)}, ${(FLOOR + 70).toFixed(1)}, y); }`;
  // A see-through layer (skin, bone): faint where you look straight at it,
  // stronger where it turns away, so the outline reads and the inside shows.
  // Each layer is drawn twice: first only its depth, so that just its nearest
  // surface is coloured and the layer does not pile up on itself.
  const ghost = (color, faceOn, edgeOn, power, glow) => new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uFace: { value: faceOn }, uEdge: { value: edgeOn }, uPower: { value: power }, uGlow: { value: glow } },
    vertexShader: VERTEX,
    fragmentShader: `
      uniform vec3 uColor; uniform float uFace, uEdge, uPower, uGlow;
      varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace;
      ${LIGHT}
      void main() {
        vec3 n = normalize(vNormal), v = normalize(vView);
        if (dot(n, v) < 0.0) n = -n;
        float edge = pow(1.0 - dot(n, v), uPower);
        float lit = 0.55 + 0.45 * max(dot(n, normalize(KEY)), 0.0) + 0.15 * max(dot(n, normalize(FILL)), 0.0);
        gl_FragColor = vec4(uColor * (lit + uGlow * edge), (uFace + (uEdge - uFace) * edge) * fadeOut(vPlace.y));
      }`,
    transparent: true, depthWrite: false, depthFunc: THREE.LessEqualDepth, side: THREE.DoubleSide,
  });
  const DEPTH_ONLY = new THREE.MeshBasicMaterial({ colorWrite: false, side: THREE.DoubleSide, transparent: true });
  // Brain tissue. Its colour is set from the model: `tag` says which of the two
  // zones a point belongs to, and `value` is how deep it sits in a fold.
  const TISSUE = new THREE.ShaderMaterial({
    uniforms: { uFront: { value: new THREE.Color() }, uBack: { value: new THREE.Color() }, uFolds: { value: 1 }, uLeaves: { value: 0 }, uFan: { value: new THREE.Vector2() } },
    vertexShader: VERTEX,
    fragmentShader: `
      uniform vec3 uFront, uBack; uniform float uFolds, uLeaves; uniform vec2 uFan;
      varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace; varying float vTag; varying float vValue;
      ${LIGHT}
      void main() {
        vec3 n = normalize(vNormal), v = normalize(vView);
        if (dot(n, v) < 0.0) n = -n;
        float open = 1.0 - uFolds * smoothstep(1.5, 13.0, vValue);                 // 1 on the crowns, 0 deep in a fold
        if (uLeaves > 0.5) {                                                       // cerebellum: thin leaves, drawn as a pattern
          float turn = atan(vPlace.y - uFan.y, vPlace.x - uFan.x);
          open *= 0.38 + 0.62 * smoothstep(0.0, 0.55, abs(sin(turn * 52.0)));
        }
        float key = max(dot(n, normalize(KEY)), 0.0), fill = max(dot(n, normalize(FILL)), 0.0);
        float lit = (0.26 + 0.66 * key + 0.16 * fill) * (0.22 + 0.78 * open);
        float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0);
        float shine = pow(max(dot(n, normalize(normalize(KEY) + v)), 0.0), 36.0) * open;   // a wet highlight
        vec3 colour = mix(uFront, uBack, step(0.5, mod(vTag, 2.0)));
        gl_FragColor = vec4(colour * lit + colour * rim * 0.22 + vec3(0.22) * shine * dot(colour, vec3(0.5)), 1.0);
      }`,
  });
  const tissue = (folds, leaves = 0) => { const m = TISSUE.clone(); m.uniforms.uFolds.value = folds; m.uniforms.uLeaves.value = leaves; return m; };
  // Arteries. `tag` carries the zone (front or back) and marks the two carotid
  // trunks; `value` is the distance along the artery from the neck, used to
  // draw pulses that travel upward at a speed set by the model's flow.
  const P = D.anchors.pinch;
  const VESSEL = new THREE.ShaderMaterial({
    uniforms: {
      uDim: { value: [new THREE.Color(), new THREE.Color()] }, uBright: { value: [new THREE.Color(), new THREE.Color()] },
      uPhase: { value: new THREE.Vector2() }, uPulse: { value: new THREE.Vector2() }, uSqueeze: { value: 0 },
      uPinchLeft: { value: new V3(...P.left) }, uPinchRight: { value: new V3(...P.right) },
    },
    vertexShader: `
      attribute float tag; attribute float value;
      uniform float uSqueeze; uniform vec3 uPinchLeft, uPinchRight;
      varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace; varying float vZone; varying float vValue;
      void main() {
        vec3 p = position;
        float trunk = floor(tag / 2.0 + 0.25);                                     // 0 none, 1 left carotid, 2 right carotid
        if (trunk > 0.5) {                                                         // squeeze the trunk toward its middle
          vec3 c = trunk < 1.5 ? uPinchLeft : uPinchRight;
          float k = 0.88 * uSqueeze * exp(-pow((p.y - c.y) / 13.0, 2.0));
          p.xz = mix(p.xz, c.xz, k);
        }
        vec4 eye = modelViewMatrix * vec4(p, 1.0);
        vNormal = normalMatrix * normal; vView = -eye.xyz; vPlace = p; vZone = mod(tag, 2.0); vValue = value;
        gl_Position = projectionMatrix * eye;
      }`,
    fragmentShader: `
      uniform vec3 uDim[2]; uniform vec3 uBright[2]; uniform vec2 uPhase, uPulse;
      varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace; varying float vZone; varying float vValue;
      ${LIGHT}
      void main() {
        vec3 n = normalize(vNormal), v = normalize(vView);
        if (dot(n, v) < 0.0) n = -n;
        bool back = vZone > 0.5;
        float wave = fract((vValue - (back ? uPhase.y : uPhase.x)) / 46.0);
        float pulse = smoothstep(0.0, 0.12, wave) * (1.0 - smoothstep(0.12, 0.55, wave)) * (back ? uPulse.y : uPulse.x);
        vec3 base = back ? uDim[1] : uDim[0], bright = back ? uBright[1] : uBright[0];
        float lit = 0.42 + 0.62 * max(dot(n, normalize(KEY)), 0.0) + 0.2 * max(dot(n, normalize(FILL)), 0.0);
        float shine = pow(max(dot(n, normalize(normalize(KEY) + v)), 0.0), 24.0);
        gl_FragColor = vec4((mix(base, bright, pulse) * lit + vec3(0.3) * shine * dot(base, vec3(0.6))) * fadeOut(vPlace.y), 1.0);
      }`,
  });
  const flat = (color) => new THREE.MeshBasicMaterial({ color });
  const lit = (color) => new THREE.ShaderMaterial({                  // a plain shaded solid (eyeball, eyelids)
    uniforms: { uColor: { value: new THREE.Color(color) } }, vertexShader: VERTEX,
    fragmentShader: `uniform vec3 uColor; varying vec3 vNormal; varying vec3 vView; ${LIGHT}
      void main() { vec3 n = normalize(vNormal); gl_FragColor = vec4(uColor * (0.5 + 0.6 * max(dot(n, normalize(KEY)), 0.0) + 0.2 * max(dot(n, normalize(FILL)), 0.0)), 1.0); }`,
  });

  // ---- scene ------------------------------------------------------------------
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);
  host.appendChild(renderer.domElement);
  const scene = new THREE.Scene(), model = new THREE.Group();
  scene.add(model);
  const TALL = 800;                                    // how much of the scene, top to bottom, the view shows
  const camera = new THREE.PerspectiveCamera(26, A.size[0] / A.size[1], 400, 6000);
  camera.position.set(0, -10, (TALL / 2) / Math.tan((13 * Math.PI) / 180));
  camera.lookAt(0, -10, 0);
  const add = (geometry, material, order) => { const m = new THREE.Mesh(geometry, material); m.renderOrder = order; model.add(m); return m; };
  const layer = (geometry, material, order) => { add(geometry, DEPTH_ONLY, order); add(geometry, material, order + 1); };

  // Solid things first: brain, arteries, eyes. Then bone and skin over them.
  const cortex = tissue(1), stem = tissue(0), leafy = tissue(0, 1), tissues = [cortex, stem, leafy];
  add(unpack(D.meshes.cortex), cortex, 1);
  add(unpack(D.meshes.whiteMatter), cortex, 1);
  add(unpack(D.meshes.brainstem), stem, 1);
  // The cerebellum's leaves are a pattern fanned out from a point just in front of it, not real folds.
  const lobe = D.meshes.cerebellum;
  leafy.uniforms.uFan.value.set(lobe.low[0] - 30, (lobe.low[1] + lobe.high[1]) / 2 + 12);
  add(unpack(lobe), leafy, 1);
  add(unpack(D.meshes.arteries), VESSEL, 2);
  const BONE = ghost(0xdfe9f2, 0.1, 0.72, 1.6, 0.25), TOOTH = ghost(0xf2f6fa, 0.5, 0.9, 1.4, 0.15), SKIN = ghost(0x8fb9dc, 0.035, 0.6, 2.4, 0.5);
  for (const name of ["skull", "mandible", "spine"]) layer(unpack(D.meshes[name]), BONE, 10);
  layer(unpack(D.meshes.teeth), TOOTH, 12);
  layer(unpack(D.meshes.skin), SKIN, 20);

  // Rings that close on each carotid where it is compressed.
  const rings = ["left", "right"].map((side) => {
    const ring = add(new THREE.TorusGeometry(15, 2, 8, 32), flat(0xeaf2fa), 3);
    ring.position.set(...P[side]); ring.rotation.x = Math.PI / 2; ring.visible = false;
    return ring;
  });

  // ---- eyes -------------------------------------------------------------------
  // The eyeballs sit where the source model has them and look straight ahead.
  // Each is a faint ball with a solid almond-shaped front: the white, the iris
  // and the pupil. The white and both lids are slices of a sphere whose two
  // poles are the corners of the eye, so the upper lid hinges there to shut.
  const lids = [], OPEN = 0.33;                        // half the opening, as an angle seen from the middle of the eye
  const BALL = ghost(0xcfe0ee, 0.1, 0.5, 1.6, 0.2), LID = lit(0x4d6a85);
  for (const e of D.eyes) {
    const eye = new THREE.Group(), r = e.radius; eye.position.set(...e.centre); model.add(eye);
    const part = (geometry, material, order = 3) => { const m = new THREE.Mesh(geometry, material); m.renderOrder = order; eye.add(m); return m; };
    const slice = (radius, from, to, material) => {
      const g = new THREE.SphereGeometry(radius, 12, 24, from, to - from, 0.5, Math.PI - 1.0); g.rotateX(Math.PI / 2);
      return part(g, material);
    };
    part(new THREE.SphereGeometry(r, 32, 20), BALL, 13);
    slice(r, -OPEN, OPEN, lit(0xbcc9d4));
    const cap = (radius, angle, material) => {         // a round patch on the front of the ball
      const g = new THREE.SphereGeometry(radius, 28, 6, 0, 2 * Math.PI, 0, angle); g.rotateZ(Math.PI / 2);
      return part(g, material);
    };
    cap(r * 1.012, 0.4, lit(0x3a78ad)); cap(r * 1.024, 0.17, flat(0x03070b));
    lids.push(slice(r * 1.06, -OPEN - 2 * OPEN - 0.1, -OPEN, LID)); slice(r * 1.06, OPEN, OPEN + 0.5, LID);
  }

  // ---- labels (drawn over the 3D view) ----------------------------------------
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "overlay"); host.appendChild(svg);
  const LABELS = [
    { name: "front of the brain", short: "front", note: "carotid supply", at: D.anchors.frontOfBrain, out: 34, spot: [0.035, 0.17] },
    { name: "back of the brain", short: "back", note: "vertebral supply", at: D.anchors.backOfBrain, out: 30, spot: [0.965, 0.66] },
    { name: "carotid artery", short: "carotid", at: D.anchors.carotid, out: 0, spot: [0.035, 0.95] },
    { name: "vertebral artery", short: "vertebral", at: D.anchors.vertebral, out: 0, spot: [0.965, 0.9] },
    { name: "carotid arteries compressed", short: "compressed", at: P, out: 14, spot: [0.035, 0.85], when: "held" },
  ];
  const labels = LABELS.map((l) => {
    const line = document.createElementNS(svg.namespaceURI, "line"), dot = document.createElementNS(svg.namespaceURI, "circle");
    const text = document.createElementNS(svg.namespaceURI, "text"), sub = document.createElementNS(svg.namespaceURI, "text");
    dot.setAttribute("r", 2.4); sub.setAttribute("class", "sub");
    for (const el of [line, dot, text, sub]) svg.appendChild(el);
    return { ...l, line, dot, text, sub };
  });
  const tag = document.createElement("div"); tag.className = "tag3d"; host.appendChild(tag);

  // ---- turning the head ---------------------------------------------------------
  let yaw = 0.6, pitch = 0.05, touched = false, dragging = null, width = 1, height = 1;
  const canvas = renderer.domElement;
  canvas.addEventListener("pointerdown", (e) => { dragging = { x: e.clientX, y: e.clientY, mouse: e.pointerType === "mouse" }; touched = true; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    yaw += (e.clientX - dragging.x) * 0.008;
    if (dragging.mouse) pitch = clamp(pitch + (e.clientY - dragging.y) * 0.006, -0.6, 0.6);
    dragging.x = e.clientX; dragging.y = e.clientY;
  });
  for (const type of ["pointerup", "pointercancel"]) canvas.addEventListener(type, () => { dragging = null; });
  canvas.addEventListener("keydown", (e) => {
    const step = { ArrowLeft: [-0.15, 0], ArrowRight: [0.15, 0], ArrowUp: [0, -0.1], ArrowDown: [0, 0.1] }[e.key];
    if (!step) return;
    yaw += step[0]; pitch = clamp(pitch + step[1], -0.6, 0.6); touched = true; e.preventDefault();
  });
  canvas.tabIndex = 0; canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", "3D model of a head and neck showing blood flow to the brain. Drag, or use the arrow keys, to rotate.");

  function resize() {
    width = host.clientWidth || A.size[0]; height = (width * A.size[1]) / A.size[0];
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  }

  // Brain colour: warm when the zone has its normal oxygen, cold as it nears
  // the model's threshold, dark below it.
  const WARM = [236, 164, 150], COLD = [74, 98, 132], DARK = [30, 42, 60];
  const blend = (a, b, f) => a.map((v, i) => (v + (b[i] - v) * f) / 255);
  const tissueColour = (level, off) => (off ? blend(DARK, COLD, 0.35) : blend(COLD, WARM, level));
  const scratch = new V3();
  let lastSeconds = null;
  const phase = { front: 0, back: 0 };
  // Draw one frame. `state` carries the model's numbers for this instant.
  function render(state, seconds) {
    const dt = lastSeconds === null ? 0 : clamp(seconds - lastSeconds, 0, 0.1);
    lastSeconds = seconds;
    if (!touched && !state.still) yaw = 0.6 + 0.22 * Math.sin(seconds * 0.35);
    model.rotation.set(pitch, yaw, 0, "XYZ");
    const front = tissueColour(state.level.front, state.frontOff), back = tissueColour(state.level.back, state.backOff);
    for (const m of tissues) { m.uniforms.uFront.value.setRGB(...(m === cortex ? front : back)); m.uniforms.uBack.value.setRGB(...back); }
    ["front", "back"].forEach((zone, i) => {
      const f = state.flow[zone], strength = Math.pow(f, 0.6);
      if (state.moving) phase[zone] += 150 * f * dt;
      VESSEL.uniforms.uDim.value[i].setRGB(...blend([62, 40, 54], [196, 30, 40], strength));
      VESSEL.uniforms.uBright.value[i].setRGB(...blend([84, 52, 66], [255, 150, 128], strength));
    });
    VESSEL.uniforms.uPhase.value.set(phase.front, phase.back);
    VESSEL.uniforms.uPulse.value.set(Math.min(1, state.flow.front * 4), Math.min(1, state.flow.back * 4));
    VESSEL.uniforms.uSqueeze.value = state.squeeze;
    for (const ring of rings) { ring.visible = state.squeeze > 0; const k = 1 - 0.5 * state.squeeze; ring.scale.set(k, k, 1); }
    for (const lid of lids) lid.rotation.z = (1 - state.eye) * 2 * OPEN;         // swings forward and down to shut
    renderer.render(scene, camera);

    // Labels: each has a fixed spot at the edge and a line to its place on the head.
    const near = Math.cos(yaw) >= 0 ? "left" : "right";          // which side of the head faces the viewer
    model.updateMatrixWorld();
    const project = (p, out = 0) => {
      scratch.set(p[0], p[1], p[2] + Math.sign(p[2]) * out).applyMatrix4(model.matrixWorld).project(camera);
      return [(scratch.x * 0.5 + 0.5) * width, (-scratch.y * 0.5 + 0.5) * height];
    };
    for (const l of labels) {
      const show = !l.when || state[l.when];
      for (const el of [l.line, l.dot, l.text, l.sub]) el.style.display = show ? "" : "none";
      if (!show) continue;
      const [ax, ay] = project(l.at[near], l.out);
      const sx = near === "left" ? l.spot[0] : 1 - l.spot[0];   // labels swap sides when the head faces the other way
      const right = sx > 0.5, lx = sx * width, ly = l.spot[1] * height;
      l.line.setAttribute("x1", ax); l.line.setAttribute("y1", ay); l.line.setAttribute("x2", lx + (right ? -6 : 6)); l.line.setAttribute("y2", ly - 5);
      l.dot.setAttribute("cx", ax); l.dot.setAttribute("cy", ay);
      const narrow = width < 520;
      for (const [el, textValue, dy] of [[l.text, narrow ? l.short : l.name, 0], [l.sub, narrow ? "" : l.note || "", 17]]) {
        el.textContent = textValue; el.setAttribute("x", lx); el.setAttribute("y", ly + dy); el.setAttribute("text-anchor", right ? "end" : "start");
      }
    }
    tag.style.display = state.frontOff ? "" : "none";
    if (state.frontOff) {
      const [x, y] = project(D.anchors.brainCentre);
      tag.textContent = width < 520 ? "below threshold" : "below the model's threshold";
      tag.style.left = `${(x / width) * 100}%`; tag.style.top = `${(y / height) * 100}%`;
    }
  }

  resize();
  return { render, resize, setView: (y, p) => { yaw = y; pitch = p; touched = true; } };
}

if (typeof module !== "undefined") module.exports = buildHead3D;
